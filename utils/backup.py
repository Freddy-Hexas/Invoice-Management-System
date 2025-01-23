import os
import shutil
import sqlite3
from datetime import datetime
import threading
import time

class BackupManager:
    def __init__(self, db_path, backup_dir='./backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        # 启动备份线程
        self.backup_thread = threading.Thread(target=self._backup_loop, daemon=True)
        self.backup_thread.start()
    
    def _backup_loop(self):
        """定期备份循环"""
        while True:
            try:
                self.create_backup()
                # 每周备份一次
                time.sleep(7 * 24 * 60 * 60)
            except Exception as e:
                print(f"Backup error: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再试
    
    def create_backup(self):
        """创建数据库备份"""
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(self.backup_dir, f'invoices_backup_{timestamp}.db')
        
        # 确保数据库连接已关闭
        conn = sqlite3.connect(self.db_path)
        conn.close()
        
        # 复制数据库文件
        shutil.copy2(self.db_path, backup_path)
        
        # 清理旧备份（只保留最近5个）
        self._cleanup_old_backups()
    
    def _cleanup_old_backups(self):
        """清理旧的备份文件"""
        backups = sorted([
            os.path.join(self.backup_dir, f) 
            for f in os.listdir(self.backup_dir) 
            if f.startswith('invoices_backup_')
        ])
        
        # 保留最近5个备份
        while len(backups) > 5:
            try:
                os.remove(backups.pop(0))
            except OSError:
                pass 