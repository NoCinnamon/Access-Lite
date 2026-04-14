const express = require('express');
const fs = require('fs');
const { MongoClient, ObjectId } = require('mongodb');
const path = require('path'); // Only define this once
const dotenv = require('dotenv');
const app = express();
app.use(express.json());
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

const projectRoot = path.join(__dirname, '..');
const MEMBERS_CSV = path.join(projectRoot, 'data', 'members.csv');
const CAMERA_ALERT_SETTINGS = path.join(projectRoot, 'data', 'camera_alert_settings.json');
const MEMBERS_CSV_HEADER = ['faceKey', 'name', 'memberID', 'photoPath', 'contact', 'notes'];

function readCameraAlertSettings() {
    try {
        if (!fs.existsSync(CAMERA_ALERT_SETTINGS)) {
            return { redListSoundEnabled: true };
        }
        const raw = fs.readFileSync(CAMERA_ALERT_SETTINGS, 'utf8');
        const j = JSON.parse(raw);
        return { redListSoundEnabled: j.redListSoundEnabled !== false };
    } catch (e) {
        return { redListSoundEnabled: true };
    }
}

function writeCameraAlertSettings(settings) {
    fs.mkdirSync(path.dirname(CAMERA_ALERT_SETTINGS), { recursive: true });
    const payload = {
        redListSoundEnabled: settings.redListSoundEnabled !== false,
    };
    fs.writeFileSync(CAMERA_ALERT_SETTINGS, `${JSON.stringify(payload)}\n`, 'utf8');
}

app.use('/known_faces', express.static(path.join(projectRoot, 'known_faces')));


const result = dotenv.config({ path: path.join(__dirname, '..', '.env') });

if (result.error) {
    console.error("❌ DOTENV ERROR:", result.error);
} else {
    console.log("✅ .env file loaded successfully");
    if (process.env.ALLOW_ADMIN_REGISTER === 'true') {
        console.warn('⚠️ ALLOW_ADMIN_REGISTER=true — POST /api/admin/register is open; disable after setup.');
    }
}

// CRITICAL: Ensure 'MONGO_URL' matches what is inside your .env file!
const url = process.env.MONGO_URL || process.env.MONGO_URI; 
const dbName = 'attendence'; 

let db;

// Open the site at / on the login page (not index.html, which is the dashboard).
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'login.html'));
});

// Serve your frontend files (index.html, style.css, etc.)
app.use(express.static(__dirname));

app.get('/api/logs', async (req, res) => {
    try {
        if (!db) {
            throw new Error("The 'db' variable is undefined. Check your connection logic.");
        }

        const logs = await db.collection('Attendance-Logs').find({}).toArray();
        console.log(`Success! Found ${logs.length} logs.`);
        res.json(logs);
    } catch (err) {
        console.error("CRITICAL DATABASE ERROR:", err.message);
        res.status(500).json({ error: err.message });
    }
});

/** Names recognized as Arrived during the current recording session (from Python stdout). */
const sessionDetectedNames = new Set();

/** Filename stem "DisplayName-MemberID" split on last hyphen (same as Python). */
function parseFaceFilenameStem(stem) {
    const s = String(stem || '').trim();
    if (!s) return { name: s, memberID: s, faceKey: s };
    const idx = s.lastIndexOf('-');
    if (idx <= 0) return { name: s, memberID: s, faceKey: s };
    const memberID = s.slice(idx + 1).trim();
    const name = s.slice(0, idx).trim();
    if (!memberID) return { name: s, memberID: s, faceKey: s };
    return { name, memberID, faceKey: s };
}

function escapeCsvField(val) {
    const str = String(val ?? '');
    if (/[",\n\r]/.test(str)) return `"${str.replace(/"/g, '""')}"`;
    return str;
}

function parseCsvLine(line) {
    const out = [];
    let cur = '';
    let inQuotes = false;
    for (let i = 0; i < line.length; i++) {
        const c = line[i];
        if (inQuotes) {
            if (c === '"') {
                if (line[i + 1] === '"') {
                    cur += '"';
                    i++;
                } else {
                    inQuotes = false;
                }
            } else {
                cur += c;
            }
        } else if (c === '"') {
            inQuotes = true;
        } else if (c === ',') {
            out.push(cur.trim());
            cur = '';
        } else {
            cur += c;
        }
    }
    out.push(cur.trim());
    return out;
}

const knownFacesDir = path.join(projectRoot, 'known_faces');

/** Rows from known_faces only; photoPath like known_faces/Friend-4.png */
function buildMemberRowsFromPhotos() {
    const kf = knownFacesDir;
    if (!fs.existsSync(kf)) return [];
    const out = [];
    for (const f of fs.readdirSync(kf)) {
        if (!/\.(png|jpg|jpeg|webp)$/i.test(f)) continue;
        const stem = path.parse(f).name;
        const p = parseFaceFilenameStem(stem);
        out.push({
            faceKey: p.faceKey,
            name: p.name,
            memberID: p.memberID,
            photoPath: `known_faces/${f}`,
            contact: '',
            notes: '',
        });
    }
    return out;
}

function readMembersCsvMap() {
    const map = new Map();
    if (!fs.existsSync(MEMBERS_CSV) || fs.statSync(MEMBERS_CSV).size === 0) return map;
    const text = fs.readFileSync(MEMBERS_CSV, 'utf8');
    const lines = text.split(/\r?\n/).filter((l) => l.trim());
    if (lines.length < 2) return map;
    const header = parseCsvLine(lines[0]).map((h) => h.trim().toLowerCase());
    const idx = (name) => header.indexOf(name.toLowerCase());
    const iFk = idx('facekey');
    const iName = idx('name');
    const iMid = idx('memberid');
    const iPhoto = idx('photopath');
    const iContact = idx('contact');
    const iNotes = idx('notes');
    if (iFk < 0) return map;
    for (let r = 1; r < lines.length; r++) {
        const cells = parseCsvLine(lines[r]);
        const fk = cells[iFk]?.trim();
        if (!fk) continue;
        map.set(fk, {
            faceKey: fk,
            name: iName >= 0 ? cells[iName] || '' : '',
            memberID: iMid >= 0 ? cells[iMid] || '' : '',
            photoPath: iPhoto >= 0 ? cells[iPhoto] || '' : '',
            contact: iContact >= 0 ? cells[iContact] || '' : '',
            notes: iNotes >= 0 ? cells[iNotes] || '' : '',
        });
    }
    return map;
}

function writeMembersCsvRows(rows) {
    fs.mkdirSync(path.dirname(MEMBERS_CSV), { recursive: true });
    const sorted = [...rows].sort((a, b) => String(a.faceKey).localeCompare(String(b.faceKey)));
    const lines = [MEMBERS_CSV_HEADER.join(',')];
    for (const m of sorted) {
        lines.push(
            [
                escapeCsvField(m.faceKey),
                escapeCsvField(m.name),
                escapeCsvField(m.memberID),
                escapeCsvField(m.photoPath),
                escapeCsvField(m.contact),
                escapeCsvField(m.notes),
            ].join(',')
        );
    }
    fs.writeFileSync(MEMBERS_CSV, `${lines.join('\n')}\n`, 'utf8');
}

/**
 * Merge CSV contact/notes into rows derived from known_faces filenames.
 * Rewrites data/members.csv and upserts MongoDB `members`.
 */
async function syncMembersCsvAndDb(database) {
    const fromPhotos = buildMemberRowsFromPhotos();
    const csvMap = readMembersCsvMap();
    const merged = fromPhotos.map((row) => {
        const csv = csvMap.get(row.faceKey);
        return {
            faceKey: row.faceKey,
            name: row.name,
            memberID: row.memberID,
            photoPath: row.photoPath,
            contact: csv && csv.contact != null ? String(csv.contact) : '',
            notes: csv && csv.notes != null ? String(csv.notes) : '',
        };
    });
    writeMembersCsvRows(merged);
    const keys = merged.map((m) => m.faceKey);
    if (keys.length === 0) {
        await database.collection('members').deleteMany({});
        return 0;
    }
    await database.collection('members').deleteMany({ faceKey: { $nin: keys } });
    const now = new Date();
    for (const m of merged) {
        await database.collection('members').updateOne(
            { faceKey: m.faceKey },
            {
                $set: { ...m, updatedAt: now },
                $setOnInsert: { createdAt: now },
            },
            { upsert: true }
        );
    }
    for (const [fk, csvRow] of csvMap) {
        if (!keys.includes(fk)) {
            console.warn(`members.csv: faceKey "${fk}" has no matching file in known_faces — skipped`);
        }
    }
    return merged.length;
}

let knownFacesSyncTimer = null;
let knownFacesSyncChain = Promise.resolve();

function scheduleKnownFacesSync(reason) {
    if (!db) return;
    if (knownFacesSyncTimer) clearTimeout(knownFacesSyncTimer);
    knownFacesSyncTimer = setTimeout(() => {
        knownFacesSyncTimer = null;
        knownFacesSyncChain = knownFacesSyncChain.then(async () => {
            try {
                const n = await syncMembersCsvAndDb(db);
                console.log(
                    `Members auto-sync (${reason}): ${n} row(s) → data/members.csv + MongoDB "members"`,
                );
            } catch (e) {
                console.error('Members auto-sync failed:', e.message);
            }
        });
    }, 450);
}

function startKnownFacesWatcher() {
    try {
        if (!fs.existsSync(knownFacesDir)) {
            fs.mkdirSync(knownFacesDir, { recursive: true });
        }
    } catch (e) {
        console.error('Could not ensure known_faces exists:', e.message);
        return;
    }
    try {
        fs.watch(knownFacesDir, { persistent: true }, (eventType, filename) => {
            if (filename != null && filename !== '') {
                if (!/\.(png|jpg|jpeg|webp)$/i.test(filename)) return;
            }
            scheduleKnownFacesSync(
                filename ? `known_faces/${filename}` : String(eventType || 'change'),
            );
        });
        console.log('Watching known_faces/ — new or updated photos sync to members.csv + DB');
    } catch (e) {
        console.error('Could not watch known_faces:', e.message);
    }
}

async function rewriteMembersCsvFromDb(database) {
    const rows = await database.collection('members').find({}).sort({ faceKey: 1 }).toArray();
    const plain = rows.map((d) => ({
        faceKey: d.faceKey,
        name: d.name,
        memberID: d.memberID,
        photoPath: d.photoPath,
        contact: d.contact ?? '',
        notes: d.notes ?? '',
    }));
    writeMembersCsvRows(plain);
}

function ingestStdoutForDetections(chunk, bufferRef) {
    bufferRef.value += chunk.toString('utf8');
    const parts = bufferRef.value.split(/\r?\n/);
    bufferRef.value = parts.pop() || '';
    const reEntry = /ENTRY\s+RECORDED:\s*(.+?)\s+marked\s+as\s+Arrived/i;
    const reKeys = /^SESSION_DETECT_KEYS:\s*(.+)$/i;
    for (const line of parts) {
        const clean = line.replace(/\r$/, '');
        const mEntry = clean.match(reEntry);
        if (mEntry) {
            const name = mEntry[1].trim();
            if (name) {
                sessionDetectedNames.add(name);
                console.log(`Session detection: ${name}`);
            }
        }
        const mKeys = clean.match(reKeys);
        if (mKeys) {
            for (const part of mKeys[1].split('|')) {
                const k = part.trim();
                if (k) {
                    sessionDetectedNames.add(k);
                    console.log(`Session detection key: ${k}`);
                }
            }
        }
    }
}

const getMembersHandler = async (req, res) => {
    try {
        if (!db) {
            return res.status(503).json({ error: 'Database not connected' });
        }
        const members = await db
            .collection('members')
            .find({})
            .sort({ faceKey: 1 })
            .toArray();
        res.json(members);
    } catch (err) {
        console.error('GET /api/members:', err.message);
        res.status(500).json({ error: err.message });
    }
};
app.get('/api/members', getMembersHandler);
app.get('/api/students', getMembersHandler); // legacy alias

const putMembersHandler = async (req, res) => {
    try {
        if (!db) {
            return res.status(503).json({ error: 'Database not connected' });
        }
        const body = req.body || {};
        const { faceKey, name, contact, notes } = body;
        const memberID = body.memberID != null ? body.memberID : body.studentID;
        const fk = faceKey != null && String(faceKey).trim();
        if (!fk) {
            return res.status(400).json({ error: 'faceKey is required (photo filename without extension)' });
        }
        const diskRow = buildMemberRowsFromPhotos().find((r) => r.faceKey === fk);
        if (!diskRow) {
            return res.status(404).json({
                error: `No photo in known_faces for face key "${fk}". Add Name-MemberID.ext first, then Sync.`,
            });
        }
        if (memberID == null || String(memberID).trim() === '' || name == null || String(name).trim() === '') {
            return res.status(400).json({ error: 'Member ID and name are required' });
        }
        const doc = {
            faceKey: fk,
            memberID: String(memberID).trim(),
            name: String(name).trim(),
            photoPath: diskRow.photoPath,
            contact: contact != null ? String(contact) : '',
            notes: notes != null ? String(notes) : '',
            updatedAt: new Date(),
        };
        await db.collection('members').updateOne(
            { faceKey: fk },
            { $set: doc, $setOnInsert: { createdAt: new Date() } },
            { upsert: true }
        );
        await rewriteMembersCsvFromDb(db);
        const saved = await db.collection('members').findOne({ faceKey: fk });
        res.json(saved);
    } catch (err) {
        console.error('PUT /api/members:', err.message);
        res.status(500).json({ error: err.message });
    }
};
app.put('/api/members', putMembersHandler);
app.put('/api/students', putMembersHandler); // legacy alias

app.post('/api/members/sync', async (req, res) => {
    try {
        if (!db) {
            return res.status(503).json({ error: 'Database not connected' });
        }
        const n = await syncMembersCsvAndDb(db);
        res.json({ ok: true, count: n, csv: MEMBERS_CSV });
    } catch (err) {
        console.error('POST /api/members/sync:', err.message);
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/session-detections', (req, res) => {
    res.json({
        detectedNames: Array.from(sessionDetectedNames),
        recording: Boolean(pythonProcess),
    });
});

/** Red-list alert sound only (Python reads JSON); not used for detection or logging. */
app.get('/api/settings/camera-alerts', (req, res) => {
    try {
        res.json(readCameraAlertSettings());
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.put('/api/settings/camera-alerts', (req, res) => {
    try {
        const b = req.body || {};
        if (typeof b.redListSoundEnabled !== 'boolean') {
            return res.status(400).json({ error: 'redListSoundEnabled (boolean) is required' });
        }
        writeCameraAlertSettings({ redListSoundEnabled: b.redListSoundEnabled });
        res.json(readCameraAlertSettings());
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// 1. Connect to MongoDB FIRST
if (!url) {
    console.error("ERROR: No Connection URL found. Check your .env file name and path!");
} else {
    MongoClient.connect(url)
        .then(async (client) => {
            db = client.db(dbName);
            console.log('Connected to MongoDB Atlas');
            try {
                const n = await syncMembersCsvAndDb(db);
                console.log(`Members: synced ${n} row(s) from known_faces + data/members.csv → collection "members"`);
            } catch (e) {
                console.error('Members sync on startup failed:', e.message);
            }

            startKnownFacesWatcher();

            app.listen(8001, () => {
                console.log('Access Lite Server running at http://localhost:8001');
            });
        })
        .catch((err) => {
            console.error('Connection Failed:', err.message);
        });
}

// Admin self-registration is OFF by default. Set ALLOW_ADMIN_REGISTER=true in .env only on a trusted machine for initial setup.
app.post('/api/admin/register', async (req, res) => {
    try {
        if (process.env.ALLOW_ADMIN_REGISTER !== 'true') {
            return res.status(403).json({
                error: 'Admin registration is disabled. Add users via MongoDB or enable ALLOW_ADMIN_REGISTER=true temporarily in .env.',
            });
        }

        const { username, password, email, phone } = req.body;

        if (username == null || String(username).trim() === '') {
            return res.status(400).json({ error: 'Username is required' });
        }
        if (password == null || String(password).length < 1) {
            return res.status(400).json({ error: 'Password is required' });
        }

        const emailTrim = email != null ? String(email).trim() : '';
        const phoneTrim = phone != null ? String(phone).trim() : '';

        // 1. Reference the 'Admins' collection 
        // (MongoDB creates this automatically on the first insert)
        const adminCollection = db.collection('Admins');

        // 2. Check if you already made an account
        const existingAdmin = await adminCollection.findOne({ username });
        if (existingAdmin) {
            return res.status(400).json({ error: "Admin already exists!" });
        }

        // 3. Encrypt the password
        const hashedPassword = await bcrypt.hash(password, 10);

        // 4. Insert into DB
        await adminCollection.insertOne({
            username: String(username).trim(),
            password: hashedPassword,
            email: emailTrim,
            phone: phoneTrim,
            createdAt: new Date(),
        });

        console.log(
            `✅ Admin Created: ${String(username).trim()} (email: ${emailTrim ? 'yes' : 'empty'}, phone: ${phoneTrim ? 'yes' : 'empty'})`,
        );
        res.json({
            message: 'Admin account created successfully!',
            admin: {
                username: String(username).trim(),
                email: emailTrim,
                phone: phoneTrim,
            },
        });
    } catch (err) {
        console.error("Registration Error:", err);
        res.status(500).json({ error: "Server error during registration" });
    }
});

function parseBearerAdmin(req) {
    const h = req.headers.authorization;
    if (!h || typeof h !== 'string' || !h.startsWith('Bearer ')) return null;
    try {
        return jwt.verify(h.slice(7), process.env.JWT_SECRET || 'your_secret_key');
    } catch {
        return null;
    }
}

/**
 * Load admin doc for JWT: try _id first, then username (fixes bad/stale id in token).
 */
/** Read contact fields (lowercase keys preferred; also accept common Compass typos). */
function adminEmailFromDoc(doc) {
    if (!doc) return '';
    const keys = ['email', 'Email', 'mail'];
    for (const k of keys) {
        const v = doc[k];
        if (v != null && String(v).trim() !== '') return String(v).trim();
    }
    return '';
}

function adminPhoneFromDoc(doc) {
    if (!doc) return '';
    const keys = ['phone', 'Phone', 'mobile', 'Mobile', 'tel'];
    for (const k of keys) {
        const v = doc[k];
        if (v != null && String(v).trim() !== '') return String(v).trim();
    }
    return '';
}

async function findAdminForPayload(payload) {
    if (!payload) return null;
    const col = db.collection('Admins');
    const proj = { projection: { password: 0 } };
    const idStr = payload.id != null ? String(payload.id).trim() : '';
    if (idStr && ObjectId.isValid(idStr)) {
        const byId = await col.findOne({ _id: new ObjectId(idStr) }, proj);
        if (byId) return byId;
    }
    const uname = payload.username != null ? String(payload.username).trim() : '';
    if (uname) {
        return col.findOne({ username: uname }, proj);
    }
    return null;
}

app.get('/api/admin/me', async (req, res) => {
    try {
        const payload = parseBearerAdmin(req);
        if (!payload) {
            return res.status(401).json({ error: 'Unauthorized' });
        }
        const admin = await findAdminForPayload(payload);
        if (!admin) return res.status(404).json({ error: 'Admin not found' });
        res.json({
            username: admin.username != null ? String(admin.username) : '',
            email: adminEmailFromDoc(admin),
            phone: adminPhoneFromDoc(admin),
        });
    } catch (err) {
        console.error('GET /api/admin/me:', err.message);
        res.status(401).json({ error: 'Unauthorized' });
    }
});

app.put('/api/admin/profile', async (req, res) => {
    try {
        const payload = parseBearerAdmin(req);
        if (!payload) {
            return res.status(401).json({ error: 'Unauthorized' });
        }
        const existing = await findAdminForPayload(payload);
        if (!existing || !existing._id) {
            return res.status(404).json({ error: 'Admin not found' });
        }
        const body = req.body || {};
        const email = body.email != null ? String(body.email).trim() : '';
        const phone = body.phone != null ? String(body.phone).trim() : '';
        const r = await db.collection('Admins').updateOne(
            { _id: existing._id },
            { $set: { email, phone } },
        );
        if (r.matchedCount === 0) return res.status(404).json({ error: 'Admin not found' });
        const admin = await db.collection('Admins').findOne(
            { _id: existing._id },
            { projection: { password: 0 } },
        );
        res.json({
            username: admin.username != null ? String(admin.username) : '',
            email: adminEmailFromDoc(admin),
            phone: adminPhoneFromDoc(admin),
        });
    } catch (err) {
        console.error('PUT /api/admin/profile:', err.message);
        res.status(500).json({ error: err.message });
    }
});

// --- ADMIN LOGIN ROUTE ---
app.post('/api/admin/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        // 1. Find the admin in your 'Admins' collection
        const admin = await db.collection('Admins').findOne({ username: username });

        // 2. If user doesn't exist
        if (!admin) {
            console.log(`❌ Login failed: User ${username} not found`);
            return res.status(401).json({ error: "Invalid username or password" });
        }

        // 3. Compare the typed password with the hashed password in DB
        const isMatch = await bcrypt.compare(password, admin.password);
        
        if (isMatch) {
            // 4. Create the "Key Card" (JWT Token)
            const token = jwt.sign(
                { id: String(admin._id), username: admin.username },
                process.env.JWT_SECRET || 'your_secret_key',
                { expiresIn: '2h' },
            );

            console.log(`🔑 Login successful: ${username}`);
            res.json({ status: "success", token, username: admin.username });
        } else {
            console.log(`❌ Login failed: Wrong password for ${username}`);
            res.status(401).json({ error: "Invalid username or password" });
        }
    } catch (err) {
        console.error("Login Route Error:", err);
        res.status(500).json({ error: "Server error during login" });
    }
});

const { spawn } = require('child_process');
let pythonProcess = null;

app.post('/api/toggle-camera', (req, res) => {
    if (pythonProcess) {
        pythonProcess.kill();
        pythonProcess = null;
        console.log("Stopping AI...");
        return res.json({ status: "stopped" });
    }

    sessionDetectedNames.clear();
    console.log("Launching Python AI script..."); // Log to confirm the button worked

    const scriptPath = path.join(projectRoot, 'face-recognition-frame.py');
    const stdoutBuffer = { value: '' };
    const pythonBin = process.env.PYTHON_EXEC || (process.platform === 'win32' ? 'python' : 'python3');

    pythonProcess = spawn(pythonBin, ['-u', scriptPath], {
        cwd: projectRoot,
        env: { ...process.env, PYTHONUNBUFFERED: '1' },
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`AI Output: ${data}`);
        ingestStdoutForDetections(data, stdoutBuffer);
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`AI Error: ${data}`);
    });

    pythonProcess.on('close', () => {
        pythonProcess = null;
        console.log('Python AI process exited');
    });

    res.json({ status: "started" });
});



