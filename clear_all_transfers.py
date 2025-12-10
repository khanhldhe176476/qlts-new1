#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app import app, db
from models import AssetTransfer

with app.app_context():
    count = AssetTransfer.query.count()
    print(f"Tim thay {count} ban ghi ban giao")
    
    if count > 0:
        AssetTransfer.query.delete()
        db.session.commit()
        print(f"Da xoa {count} ban ghi ban giao")
    else:
        print("Khong co ban ghi nao de xoa")

















