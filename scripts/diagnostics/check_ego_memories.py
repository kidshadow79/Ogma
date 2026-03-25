#!/usr/bin/env python3
"""Vérification rapide des ego traits redondants"""

import sqlite3

conn = sqlite3.connect('data/memory/memories.db')
c = conn.cursor()

mem_ids = ['EGO_20250916_143535_546', 'EGO_20250916_135734_138']

c.execute('SELECT id, text_original, summary FROM memories WHERE id IN (?, ?)', tuple(mem_ids))

for row in c.fetchall():
    print(f'ID: {row[0]}')
    print(f'Text: {row[1] if row[1] else "None"}')
    print(f'Summary: {row[2] if row[2] else "None"}')
    print('-' * 80)

conn.close()
