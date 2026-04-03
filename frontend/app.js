const express = require('express');
const { MongoClient } = require('mongodb');
const path = require('path'); // Only define this once
const dotenv = require('dotenv');
const app = express();
app.use(express.json());
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');


const result = dotenv.config({ path: path.join(__dirname, '..', '.env') });

if (result.error) {
    console.error("❌ DOTENV ERROR:", result.error);
} else {
    console.log("✅ .env file loaded successfully");
}

// CRITICAL: Ensure 'MONGO_URL' matches what is inside your .env file!
const url = process.env.MONGO_URL || process.env.MONGO_URI; 
const dbName = 'attendence'; 

let db;

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

// 1. Connect to MongoDB FIRST
if (!url) {
    console.error("ERROR: No Connection URL found. Check your .env file name and path!");
} else {
    MongoClient.connect(url)
        .then(client => {
            db = client.db(dbName);
            console.log('Connected to MongoDB Atlas');

            // 2. Start the Server ONLY after connection is successful
            app.listen(8001, () => {
                console.log('Access Lite Server running at http://localhost:8001');
            });
        })
        .catch(err => {
            console.error('Connection Failed:', err.message);
        });
}

// --- ADMIN REGISTRATION (Run this once to create your account) ---
app.post('/api/admin/register', async (req, res) => {
    try {
        const { username, password } = req.body;

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
            username: username,
            password: hashedPassword,
            createdAt: new Date()
        });

        console.log(`✅ Admin Created: ${username}`);
        res.json({ message: "Admin account created successfully!" });
    } catch (err) {
        console.error("Registration Error:", err);
        res.status(500).json({ error: "Server error during registration" });
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
                { id: admin._id, username: admin.username },
                process.env.JWT_SECRET || 'your_secret_key', 
                { expiresIn: '2h' }
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

    console.log("Launching Python AI script..."); // Log to confirm the button worked

    // Use the absolute path for your Mac
    const scriptPath = '/Users/jiaqi/git-project/Access-Lite/face-recognition-frame.py';

    pythonProcess = spawn('python', [scriptPath], {
        cwd: '/Users/jiaqi/git-project/Access-Lite/', // Ensures Python finds your 'jiaqi-frameTest' folder
        env: process.env // Passes your login permissions to the script
    });

    pythonProcess.stdout.on('data', (data) => {
        console.log(`AI Output: ${data}`);
    });

    pythonProcess.stderr.on('data', (data) => {
        // This is the most important part for debugging
        console.error(`AI Error: ${data}`);
    });

    res.json({ status: "started" });
});



