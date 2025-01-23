import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry
import os
import shutil
from datetime import datetime

class InvoiceDialog:
    def __init__(self, parent, pdf_dir, invoice_data=None):
        self.parent = parent
        self.pdf_dir = pdf_dir
        self.invoice_data = invoice_data
        self.result = None
        self.selected_pdf = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("编辑发票" if invoice_data else "新增发票")
        
        # 设置字体
        self.default_font = ('Microsoft YaHei UI', 15)
        
        # 配置对话框的默认字体
        self.dialog.option_add('*Font', self.default_font)
        
        # 配置ttk样式
        style = ttk.Style(self.dialog)
        style.configure('TLabel', font=self.default_font)
        style.configure('TButton', font=self.default_font)
        style.configure('TCheckbutton', font=self.default_font)
        style.configure('TRadiobutton', font=self.default_font)
        style.configure('TEntry', font=self.default_font)
        
        # 设置窗口大小
        dialog_width = 600
        dialog_height = 500
        
        # 获取屏幕尺寸
        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        
        # 设置窗口大小和位置
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # 设置模态
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 禁止调整大小
        self.dialog.resizable(False, False)
        
        # 添加内边距
        main_frame = ttk.Frame(self.dialog, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建表单
        self.create_form(main_frame)
        
        # 如果是编辑模式，填充现有数据
        if invoice_data:
            self.fill_form(invoice_data)
        
        # 设置默认焦点
        if not invoice_data:
            self.content_entry.focus()
    
    def create_form(self, parent):
        """创建表单字段"""
        # 配置Text控件的字体
        text_font = ('Microsoft YaHei UI', 15)  # Text控件的字体
        
        # 报销内容
        ttk.Label(parent, text="报销内容*:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.content_var = tk.StringVar()
        self.content_entry = ttk.Entry(parent, textvariable=self.content_var, width=40)
        self.content_entry.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
        
        # 购买平台
        ttk.Label(parent, text="购买平台:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.platform_var = tk.StringVar()
        self.platform_entry = ttk.Entry(parent, textvariable=self.platform_var, width=40)
        self.platform_entry.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
        
        # 自费/垫付
        ttk.Label(parent, text="费用类型*:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.expense_type_var = tk.StringVar(value="垫付")
        expense_frame = ttk.Frame(parent)
        expense_frame.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        ttk.Radiobutton(expense_frame, text="垫付", variable=self.expense_type_var, value="垫付").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(expense_frame, text="自费", variable=self.expense_type_var, value="自费").pack(side=tk.LEFT, padx=5)
        
        # 金额
        ttk.Label(parent, text="金额*:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(parent, textvariable=self.amount_var)
        self.amount_entry.grid(row=3, column=1, padx=5, pady=5, sticky='ew')
        
        # 备注
        ttk.Label(parent, text="备注:").grid(row=4, column=0, padx=5, pady=5, sticky='ne')
        self.note_text = tk.Text(parent, height=4, width=40, font=text_font)
        self.note_text.grid(row=4, column=1, padx=5, pady=5, sticky='ew')
        
        # PDF文件选择
        ttk.Label(parent, text="PDF文件:").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        pdf_frame = ttk.Frame(parent)
        pdf_frame.grid(row=5, column=1, padx=5, pady=5, sticky='ew')
        
        self.pdf_var = tk.StringVar()
        self.pdf_label = ttk.Label(pdf_frame, textvariable=self.pdf_var, wraplength=300)
        self.pdf_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(pdf_frame, text="选择", command=self.select_pdf).pack(side=tk.RIGHT)
        
        # 报销状态
        ttk.Label(parent, text="报销状态:").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        self.reimbursed_var = tk.BooleanVar()
        ttk.Checkbutton(parent, text="已报销", variable=self.reimbursed_var).grid(
            row=6, column=1, padx=5, pady=5, sticky='w')
        
        # 按钮区域
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="保存", command=self.save, width=15).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="取消", command=self.cancel, width=15).pack(side=tk.LEFT, padx=10)
        
        # 设置列权重
        parent.columnconfigure(1, weight=1)
    
    def fill_form(self, data):
        """填充表单数据"""
        self.content_var.set(data['content'])
        self.platform_var.set(data['platform'])
        self.expense_type_var.set(data['expense_type'])
        self.amount_var.set(str(data['amount']))
        self.note_text.delete('1.0', tk.END)
        self.note_text.insert('1.0', data['note'] or '')
        if data['pdf_path']:
            self.selected_pdf = data['pdf_path']
            self.pdf_var.set(os.path.basename(data['pdf_path']))
        self.reimbursed_var.set(data.get('reimbursed', False))
    
    def select_pdf(self):
        """选择PDF文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            self.selected_pdf = file_path
            self.pdf_var.set(os.path.basename(file_path))
    
    def validate_form(self):
        """验证表单数据"""
        if not self.content_var.get().strip():
            messagebox.showerror("错误", "请填写报销内容")
            return False
            
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("错误", "请输入有效的金额")
            return False
            
        return True
    
    def save(self):
        """保存数据"""
        if not self.validate_form():
            return
            
        # 处理PDF文件
        pdf_path = None
        if self.selected_pdf:
            # 生成新的文件名：报销内容_金额.pdf
            new_filename = f"{self.content_var.get()}_{self.amount_var.get()}.pdf"
            pdf_path = os.path.join(self.pdf_dir, new_filename)
            
            # 如果是新文件或文件发生改变，则复制到目标位置
            if not self.invoice_data or self.selected_pdf != self.invoice_data.get('pdf_path'):
                shutil.copy2(self.selected_pdf, pdf_path)
        
        self.result = {
            'content': self.content_var.get(),
            'platform': self.platform_var.get(),
            'expense_type': self.expense_type_var.get(),
            'amount': float(self.amount_var.get()),
            'note': self.note_text.get('1.0', tk.END).strip(),
            'pdf_path': pdf_path,
            'reimbursed': self.reimbursed_var.get()
        }
        
        self.dialog.destroy()
    
    def cancel(self):
        """取消操作"""
        self.dialog.destroy() 