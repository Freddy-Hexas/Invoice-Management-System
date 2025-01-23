import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import sqlite3
from .invoice_dialog import InvoiceDialog

class DetailPanel:
    def __init__(self, parent_frame, main_app):
        self.frame = ttk.LabelFrame(parent_frame, text="详细信息")
        self.main_app = main_app
        
        # 设置字体
        self.default_font = ('Microsoft YaHei UI', 15)
        
        # 配置样式
        style = ttk.Style()
        style.configure('TLabel', font=self.default_font)
        style.configure('TButton', font=self.default_font)
        
        # 创建详情字段
        self.create_fields()
        
        # 创建按钮
        self.create_buttons()
        
        # 初始化PDF路径
        self.pdf_path = None
        self.pdf_button.state(['disabled'])

    def create_fields(self):
        """创建详情字段"""
        # 创建一个框架来容纳所有字段
        fields_frame = ttk.Frame(self.frame)
        fields_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 配置列权重，使标签能够自动扩展
        fields_frame.columnconfigure(1, weight=1)
        
        # 创建各个字段标签和值
        labels = ['报销内容:', '购买平台:', '费用类型:', '金额:', '备注:', '报销状态:']
        self.value_labels = {}
        
        for i, label in enumerate(labels):
            ttk.Label(fields_frame, text=label).grid(row=i, column=0, sticky='nw', pady=5)
            value_label = ttk.Label(fields_frame, text="", wraplength=200, justify=tk.LEFT)
            value_label.grid(row=i, column=1, sticky='nw', padx=(10, 0), pady=5)
            self.value_labels[label] = value_label

    def create_buttons(self):
        """创建按钮"""
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        button_frame.grid_columnconfigure(0, weight=1)
        
        inner_button_frame = ttk.Frame(button_frame)
        inner_button_frame.grid(row=0, column=0)
        
        # 创建编辑按钮
        self.edit_button = ttk.Button(
            inner_button_frame, 
            text="编辑", 
            width=15,
            command=self.edit_invoice,
            state='disabled'  # 初始状态为禁用
        )
        self.edit_button.pack(pady=5)
        
        # 创建删除按钮
        self.delete_button = ttk.Button(
            inner_button_frame,
            text="删除",
            width=15,
            command=self.delete_invoice,
            state='disabled'  # 初始状态为禁用
        )
        self.delete_button.pack(pady=5)
        
        # 创建PDF按钮
        self.pdf_button = ttk.Button(
            inner_button_frame, 
            text="查看PDF", 
            width=15,
            command=self.view_pdf,
            state='disabled'  # 初始状态为禁用
        )
        self.pdf_button.pack(pady=5)
        
        # 创建报销状态切换按钮
        self.toggle_button = ttk.Button(
            inner_button_frame, 
            text="切换报销状态", 
            width=15,
            command=self.toggle_reimbursed_status,
            state='disabled'  # 初始状态为禁用
        )
        self.toggle_button.pack(pady=5)

    def show_details(self, invoice_data):
        """显示发票详情"""
        self.current_invoice_id = invoice_data['id']
        
        # 更新显示的值
        self.value_labels['报销内容:'].configure(text=invoice_data['content'])
        self.value_labels['购买平台:'].configure(text=invoice_data['platform'] or "")
        self.value_labels['费用类型:'].configure(text=invoice_data['expense_type'])
        self.value_labels['金额:'].configure(text=f"¥ {invoice_data['amount']:,.2f}")
        self.value_labels['备注:'].configure(text=invoice_data['note'] or "")
        self.value_labels['报销状态:'].configure(
            text="已报销" if invoice_data['reimbursed'] else "未报销"
        )
        
        # 启用所有基本按钮
        self.edit_button.state(['!disabled'])
        self.delete_button.state(['!disabled'])
        self.toggle_button.state(['!disabled'])
        
        # 只在有PDF时启用PDF按钮
        self.pdf_path = invoice_data.get('pdf_path')
        if self.pdf_path and os.path.exists(self.pdf_path):
            self.pdf_button.state(['!disabled'])
        else:
            self.pdf_button.state(['disabled'])

    def clear_details(self):
        """清空详情显示"""
        for label in self.value_labels.values():
            label.configure(text="")
        
        # 禁用所有按钮
        self.edit_button.state(['disabled'])
        self.delete_button.state(['disabled'])
        self.pdf_button.state(['disabled'])
        self.toggle_button.state(['disabled'])
        
        self.pdf_path = None
        self.current_invoice_id = None

    def edit_invoice(self):
        """编辑发票"""
        if hasattr(self, 'current_invoice_id'):
            # 直接调用主窗口的编辑方法
            self.main_app.edit_selected_invoice()
    
    def delete_invoice(self):
        """删除发票"""
        if self.current_invoice_id:
            self.main_app.delete_invoice(self.current_invoice_id)
    
    def view_pdf(self):
        """查看PDF文件"""
        if not self.pdf_path:
            messagebox.showwarning("提示", "该发票没有关联的PDF文件")
            return
        
        if not os.path.exists(self.pdf_path):
            messagebox.showerror("错误", "PDF文件不存在")
            return
        
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.pdf_path)
            else:  # Linux/Mac
                os.system(f'xdg-open "{self.pdf_path}"')
        except Exception as e:
            messagebox.showerror("错误", f"打开PDF文件时出错：\n{str(e)}")
    
    def toggle_reimbursed_status(self):
        """切换报销状态"""
        if not hasattr(self, 'current_invoice_id'):
            return
        
        try:
            conn = sqlite3.connect('invoices.db')
            cursor = conn.cursor()
            
            # 获取当前状态和内容
            cursor.execute('SELECT reimbursed, content FROM invoices WHERE id = ?', 
                         (self.current_invoice_id,))
            result = cursor.fetchone()
            
            if result is None:
                messagebox.showerror("错误", "找不到选中的发票记录")
                return
            
            current_status = result[0]
            invoice_content = result[1]
            
            # 切换状态
            new_status = not bool(current_status)
            cursor.execute('UPDATE invoices SET reimbursed = ? WHERE id = ?',
                         (new_status, self.current_invoice_id))
            
            conn.commit()
            conn.close()
            
            # 刷新显示
            self.main_app.refresh_invoice_list()
            
            # 更新当前显示的状态文本
            status_text = "已报销" if new_status else "未报销"
            self.value_labels['报销状态:'].configure(text=status_text)
            
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"更新报销状态时出错：{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败：{str(e)}") 