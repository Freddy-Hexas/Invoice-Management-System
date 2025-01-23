import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
import sqlite3
import os
from datetime import datetime
from tkinter import filedialog, messagebox
from components.invoice_dialog import InvoiceDialog
from components.detail_panel import DetailPanel
from components.treeview import InvoiceTreeview
from utils.backup import BackupManager

class InvoiceManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("发票管理系统")
        
        # 设置全局字体
        default_font = ('Microsoft YaHei UI', 15)  # 微软雅黑UI，15号
        
        # 配置所有控件的默认字体
        self.root.option_add('*Font', default_font)
        
        # 特别配置Treeview的字体
        style = ttk.Style()
        style.configure('Treeview', font=default_font)  # 设置内容字体
        style.configure('Treeview.Heading', font=default_font)  # 设置表头字体
        
        # 配置标签和按钮的字体
        style.configure('TLabel', font=default_font)
        style.configure('TButton', font=default_font)
        style.configure('TCheckbutton', font=default_font)
        style.configure('TRadiobutton', font=default_font)
        
        # 获取屏幕尺寸
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # 设置窗口全屏
        if os.name == 'nt':  # Windows
            self.root.state('zoomed')
        else:  # Linux/Mac
            self.root.geometry(f"{screen_width}x{screen_height}+0+0")
            self.root.attributes('-zoomed', True)
        
        # 确保PDF存储目录存在
        self.pdf_dir = "./invoices_pdf"
        os.makedirs(self.pdf_dir, exist_ok=True)
        
        # 初始化数据库
        self.init_database()
        
        # 初始化备份管理器
        self.backup_manager = BackupManager('invoices.db')
        
        # 创建界面
        self.create_gui()
        
        # 加载并显示所有记录
        self.refresh_invoice_list()
        
    def init_database(self):
        """初始化SQLite数据库"""
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # 创建新表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    platform TEXT,
                    expense_type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    note TEXT,
                    pdf_path TEXT,
                    reimbursed BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        conn.commit()
        conn.close()
        
    def create_gui(self):
        """创建主界面"""
        # 创建主框架
        main_frame = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建左侧框架（列表区域）
        left_frame = ttk.Frame(main_frame)
        main_frame.add(left_frame, weight=85)
        
        # 创建右侧框架（详情区域）
        right_frame = ttk.Frame(main_frame)
        main_frame.add(right_frame, weight=15)
        
        # 创建顶部操作框架
        top_frame = ttk.Frame(left_frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 创建搜索框（宽度限制）
        search_frame = ttk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, padx=5)
        ttk.Label(search_frame, text="搜索:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda name, index, mode: self.refresh_invoice_list())
        ttk.Entry(search_frame, textvariable=self.search_var, width=30).pack(side=tk.LEFT, padx=5)
        
        # 创建新增按钮（放在搜索框右边）
        ttk.Button(top_frame, text="新增", command=self.add_invoice).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="备份", command=self.backup_database).pack(side=tk.RIGHT, padx=5)
        
        # 创建发票列表
        self.invoice_tree = InvoiceTreeview(left_frame)
        
        # 创建状态栏（移到最底部）
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=15, pady=5)
        
        # 创建详情面板
        self.detail_panel = DetailPanel(right_frame, self)
        self.detail_panel.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 绑定选择事件
        self.invoice_tree.tree.bind('<<TreeviewSelect>>', self.on_select)
        
        # 更新状态栏初始统计
        self.update_statistics()
        
    def on_select(self, event):
        """处理发票选择事件"""
        selected_items = self.invoice_tree.tree.selection()
        if not selected_items:
            self.detail_panel.clear_details()
            return
        
        # 获取选中项的ID
        item_values = self.invoice_tree.tree.item(selected_items[0])['values']
        invoice_id = item_values[0]
        
        # 从数据库获取完整的发票信息
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, content, platform, expense_type, amount, note, pdf_path, reimbursed
            FROM invoices 
            WHERE id = ?
        ''', (invoice_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            invoice_data = {
                'id': row[0],
                'content': row[1],
                'platform': row[2],
                'expense_type': row[3],
                'amount': row[4],
                'note': row[5],
                'pdf_path': row[6],
                'reimbursed': bool(row[7])
            }
            # 更新详情面板
            self.detail_panel.show_details(invoice_data)
    
    def get_invoice_details(self, invoice_id):
        """从数据库获取发票详细信息"""
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, content, platform, expense_type, amount, note, pdf_path, reimbursed 
            FROM invoices 
            WHERE id = ?
        ''', (invoice_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'content': row[1],
                'platform': row[2],
                'expense_type': row[3],
                'amount': row[4],
                'note': row[5],
                'pdf_path': row[6],
                'reimbursed': bool(row[7])
            }
        return None

    def show_add_dialog(self):
        """显示新增发票对话框"""
        dialog = InvoiceDialog(self.root, self.pdf_dir)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.save_invoice(dialog.result)
            self.refresh_invoice_list()
    
    def show_edit_dialog(self, invoice_data):
        """显示编辑发票对话框"""
        dialog = InvoiceDialog(self.root, self.pdf_dir, invoice_data)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.update_invoice(dialog.result)
            self.refresh_invoice_list()
    
    def edit_selected_invoice(self):
        """编辑当前选中的发票"""
        selected_item = self.invoice_tree.get_selected_item()
        if selected_item:
            invoice_id = selected_item['values'][0]  # 获取ID
            
            # 从数据库获取完整的发票信息
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, content, platform, expense_type, amount, note, pdf_path, reimbursed
                FROM invoices 
                WHERE id = ?
            ''', (invoice_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                invoice_data = {
                    'id': row[0],
                    'content': row[1],
                    'platform': row[2],
                    'expense_type': row[3],
                    'amount': row[4],
                    'note': row[5],
                    'pdf_path': row[6],
                    'reimbursed': bool(row[7])
                }
                
                dialog = InvoiceDialog(self.root, self.pdf_dir, invoice_data)
                self.root.wait_window(dialog.dialog)
                
                if dialog.result:
                    # 确保ID被包含在更新数据中
                    dialog.result['id'] = invoice_id
                    if self.update_invoice(dialog.result):
                        self.refresh_invoice_list()

    def check_invoice_id_exists(self, invoice_id):
        """检查发票编号是否已存在"""
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM invoices WHERE id = ?', (invoice_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    def save_invoice(self, invoice_data):
        """保存新发票到数据库"""
        try:
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            
            # 获取当前系统时间
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute('''
                INSERT INTO invoices 
                (content, platform, expense_type, amount, note, pdf_path, reimbursed, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['content'],
                invoice_data['platform'],
                invoice_data['expense_type'],
                invoice_data['amount'],
                invoice_data['note'],
                invoice_data['pdf_path'],
                invoice_data['reimbursed'],
                current_time
            ))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("成功", "发票保存成功")
            return True
            
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"保存发票时出错：{str(e)}")
            return False
    
    def update_invoice(self, invoice_data):
        """更新发票信息"""
        try:
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            
            # 如果PDF路径发生变化，删除旧的PDF文件
            cursor.execute('SELECT pdf_path FROM invoices WHERE id = ?', (invoice_data['id'],))
            old_pdf = cursor.fetchone()
            if old_pdf and old_pdf[0] and old_pdf[0] != invoice_data['pdf_path']:
                try:
                    os.remove(old_pdf[0])
                except OSError:
                    pass
            
            cursor.execute('''
                UPDATE invoices
                SET content = ?, 
                    platform = ?, 
                    expense_type = ?, 
                    amount = ?, 
                    note = ?, 
                    pdf_path = ?, 
                    reimbursed = ?
                WHERE id = ?
            ''', (
                invoice_data['content'],
                invoice_data['platform'],
                invoice_data['expense_type'],
                invoice_data['amount'],
                invoice_data['note'],
                invoice_data['pdf_path'],
                invoice_data['reimbursed'],
                invoice_data['id']
            ))
            
            conn.commit()
            conn.close()
            messagebox.showinfo("成功", "发票更新成功")
            return True
            
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"更新发票时出错：{str(e)}")
            return False
    
    def on_search_change(self, *args):
        """搜索框内容变化时触发搜索"""
        self.refresh_invoice_list()
    
    def refresh_invoice_list(self):
        """刷新发票列表"""
        # 清空现有列表
        self.invoice_tree.clear_all()
        
        # 获取搜索关键词
        search_term = self.search_var.get().strip().lower()
        
        # 从数据库获取数据
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        
        if search_term:
            # 构建模糊搜索条件
            search_pattern = f"%{search_term}%"
            cursor.execute('''
                SELECT id, content, platform, expense_type, amount, reimbursed, created_at 
                FROM invoices 
                WHERE LOWER(content) LIKE ? 
                OR LOWER(platform) LIKE ? 
                OR LOWER(expense_type) LIKE ?
                ORDER BY id DESC
            ''', (search_pattern, search_pattern, search_pattern))
        else:
            # 无搜索词时显示全部
            cursor.execute('''
                SELECT id, content, platform, expense_type, amount, reimbursed, created_at 
                FROM invoices 
                ORDER BY id DESC
            ''')
        
        # 填充数据到表格
        for row in cursor.fetchall():
            # 将时间字符串转换为datetime对象
            created_at = datetime.strptime(row[6], '%Y-%m-%d %H:%M:%S') if row[6] else None
            # 使用解包操作符将前6个元素传递，然后单独传递created_at
            self.invoice_tree.insert_item(*row[:6], created_at)
        
        conn.close()
        
        # 更新统计信息
        self.update_statistics()
    
    def update_statistics(self):
        """更新统计信息"""
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        
        search_term = self.search_var.get().strip().lower()
        
        if search_term:
            search_pattern = f"%{search_term}%"
            cursor.execute('''
                SELECT COUNT(*), SUM(amount) 
                FROM invoices 
                WHERE LOWER(content) LIKE ? 
                OR LOWER(platform) LIKE ? 
                OR LOWER(expense_type) LIKE ?
            ''', (search_pattern, search_pattern, search_pattern))
        else:
            cursor.execute('SELECT COUNT(*), SUM(amount) FROM invoices')
        
        count, total = cursor.fetchone()
        count = count or 0
        total = total or 0
        
        conn.close()
        
        # 更新状态栏
        self.status_var.set(f"共 {count} 张发票   总金额: ¥ {total:,.2f}")
    
    def delete_invoice(self, invoice_id):
        """删除发票"""
        if messagebox.askyesno("确认删除", "确定要删除这张发票吗？"):
            try:
                conn = sqlite3.connect('invoices.db')
                cursor = conn.cursor()
                
                # 获取PDF路径
                cursor.execute('SELECT pdf_path FROM invoices WHERE id = ?', (invoice_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    pdf_path = result[0]
                    # 删除PDF文件
                    try:
                        os.remove(pdf_path)
                    except OSError:
                        pass  # 忽略文件删除错误
                
                # 删除数据库记录
                cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
                conn.commit()
                conn.close()
                
                # 刷新列表
                self.refresh_invoice_list()
                # 清空详情面板
                self.detail_panel.clear_details()
                
                messagebox.showinfo("成功", "发票已删除")
                
            except sqlite3.Error as e:
                messagebox.showerror("错误", f"删除发票时出错：{str(e)}")

    def add_invoice(self):
        """添加新发票"""
        dialog = InvoiceDialog(self.root, self.pdf_dir)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            if self.save_invoice(dialog.result):
                self.refresh_invoice_list()

    def delete_selected_invoice(self):
        """删除选中的发票"""
        selected_item = self.invoice_tree.tree.selection()
        if not selected_item:
            messagebox.showwarning("警告", "请先选择要删除的发票")
            return
        
        # 获取发票ID和内容
        item_values = self.invoice_tree.tree.item(selected_item)['values']
        invoice_id = item_values[0]
        invoice_content = item_values[1]
        
        # 确认删除
        if not messagebox.askyesno("确认删除", 
                                  f"确定要删除以下发票吗？\n\n"
                                  f"编号: {invoice_id}\n"
                                  f"内容: {invoice_content}"):
            return
        
        try:
            # 从数据库中删除发票
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            
            # 先获取PDF文件路径
            cursor.execute('SELECT pdf_path FROM invoices WHERE id = ?', (invoice_id,))
            pdf_path = cursor.fetchone()[0]
            
            # 删除数据库记录
            cursor.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
            conn.commit()
            conn.close()
            
            # 如果存在PDF文件，也删除它
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except OSError:
                    pass
            
            # 刷新列表
            self.refresh_invoice_list()
            
            # 清空详情面板
            self.detail_panel.clear_details()
            
            messagebox.showinfo("成功", "发票已删除")
            
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"删除发票时出错：{str(e)}")

    def backup_database(self):
        """备份数据库"""
        try:
            # 创建备份
            backup_path = self.backup_manager.create_backup()
            if backup_path:
                messagebox.showinfo("成功", f"数据库已备份到：\n{backup_path}")
            else:
                messagebox.showwarning("警告", "备份失败")
        except Exception as e:
            messagebox.showerror("错误", f"备份过程中出错：\n{str(e)}")

    def run(self):
        """运行程序"""
        # 设置窗口最小尺寸
        self.root.minsize(800, 600)
        # 运行主循环
        self.root.mainloop()

if __name__ == "__main__":
    app = InvoiceManager()
    app.run()
