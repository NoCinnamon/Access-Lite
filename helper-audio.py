import pygame

pygame.mixer.init()
pygame.mixer.music.load('声音文件路径')
pygame.mixer.music.queue('下一个声音文件路径')
pygame.mixer.music.play()
