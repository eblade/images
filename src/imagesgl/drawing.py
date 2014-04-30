#!/usr/bin/env python3

import pygame
from imagesgl.entry import COLLECTION

COLOR_BACK = pygame.Color(50, 50, 50)
COLOR_TEXT = pygame.Color(200, 200, 200)
COLOR_TEXT_BACK = pygame.Color(100, 100, 100)
COLOR_SELECTED = pygame.Color(255, 255, 255)
COLOR_MARKED = pygame.Color(20, 100, 200)
COLOR_DELETE = pygame.Color(200, 50, 50, 128)

mainFont = pygame.font.Font('Ubuntu-R.ttf', 20)

def clear_window(win):
    win.fill(COLOR_BACK)

def draw_thumbs(win, browser):
    for entry, x, y, selected in browser.thumbs(pygame.display.get_surface().get_size()):
        if not entry.thumbnail is None:
            win.blit(entry.thumbnail, (x, y))
        else:
            pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK, 
                (x, y, entry.width_thumb or browser.block_size, 
                 entry.height_thumb or browser.block_size))
        if entry.categories:
            cats = mainFont.render(str(entry.categories), False, COLOR_TEXT)
            catRect = cats.get_rect()
            catRect.topleft = (x+2, y+2)
            pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK,
                (x, y, cats.get_width() + 4, cats.get_height() + 4))
            win.blit(cats, catRect)
            if 'D' in entry.categories:
                s = pygame.Surface((entry.width_thumb or browser.block_size, 
                     entry.height_thumb or browser.block_size))
                s.set_alpha(128)
                s.fill(COLOR_DELETE)
                win.blit(s, (x,y)) 
        if entry.marked:
            s = pygame.Surface((entry.width_thumb or browser.block_size, 
                 entry.height_thumb or browser.block_size))
            s.set_alpha(128)
            s.fill(COLOR_MARKED)
            win.blit(s, (x,y)) 
        if selected:
            s = pygame.Surface((entry.width_thumb or browser.block_size, 
                 entry.height_thumb or browser.block_size))
            s.set_alpha(128)
            s.fill(COLOR_SELECTED)
            win.blit(s, (x,y)) 
        if entry.entry_type == COLLECTION:
            title = mainFont.render(str(entry.name), False, COLOR_TEXT)
            titleRect = title.get_rect()
            titleRect.topleft = (x+2, y+42)
            pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK,
                (x, y+40, title.get_width() + 4, title.get_height() + 4))
            win.blit(title, titleRect)
    title = mainFont.render(browser.title_msg, False, COLOR_TEXT)
    titleRect = title.get_rect()
    titleRect.topleft = (10, 2)
    pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK,
        (0, 0, title.get_width() + 12, title.get_height() + 4))
    win.blit(title, titleRect)

def draw_image(win, image):
    win.blit(image.zoomed or image.original, image.position(pygame.display.get_surface().get_size()))
    if image.categories:
        cats = mainFont.render(str(image.categories), False, COLOR_TEXT)
        catRect = cats.get_rect()
        catRect.topleft = (2, 2)
        pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK,
            (0, 0, cats.get_width() + 4, cats.get_height() + 4))
        win.blit(cats, catRect)

def draw_input_box(win, inputbox):
    title = mainFont.render(inputbox.display, False, COLOR_TEXT)
    titleRect = title.get_rect()
    titleRect.topleft = (10, 2)
    pygame.draw.rect(pygame.display.get_surface(), COLOR_TEXT_BACK,
        (0, 0, title.get_width() + 12, title.get_height() + 4))
    win.blit(title, titleRect)

    top = 30
    for text, selected in inputbox.selection:
        s = mainFont.render(str(text), False, 
            COLOR_TEXT_BACK if selected else COLOR_TEXT)
        sr = s.get_rect()
        sr.topleft = (10, top + 2)
        pygame.draw.rect(pygame.display.get_surface(), 
            COLOR_SELECTED if selected else COLOR_BACK,
            (0, top, s.get_width() + 12, s.get_height() + 4))
        win.blit(s, sr)
        top += s.get_height() + 4
        
