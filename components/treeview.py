from tkinter import ttk
import tkinter as tk

class InvoiceTreeview:
    def __init__(self, parent_frame):
        # 设置字体
        self.default_font = ('Microsoft YaHei UI', 15)
        
        # 创建并配置表格
        columns = ('id', 'content', 'platform', 'expense_type', 'amount', 'reimbursed', 'created_at')
        self.tree = ttk.Treeview(parent_frame, columns=columns, show='headings', style='Custom.Treeview')
        
        # 配置样式
        style = ttk.Style()
        
        # 设置行高和其他样式
        style.configure('Custom.Treeview', 
                       font=self.default_font,
                       rowheight=40)  # 增加行高
        
        # 设置表头样式
        style.configure('Custom.Treeview.Heading', 
                       font=self.default_font,
                       padding=(0, 10))  # 增加表头padding
        
        # 添加排序状态追踪
        self.sort_states = {
            'id': False,        # False 表示升序，True 表示降序
            'content': False,
            'platform': False,
            'expense_type': False,
            'amount': False,
            'reimbursed': False,
            'created_at': False
        }
        
        # 设置列标题和排序功能
        self.tree.heading('id', text='编号', command=lambda: self.sort_column('id', is_numeric=True))
        self.tree.heading('content', text='报销内容', command=lambda: self.sort_column('content'))
        self.tree.heading('platform', text='购买平台', command=lambda: self.sort_column('platform'))
        self.tree.heading('expense_type', text='费用类型', command=lambda: self.sort_column('expense_type'))
        self.tree.heading('amount', text='金额', command=lambda: self.sort_column('amount', is_numeric=True, is_currency=True))
        self.tree.heading('reimbursed', text='报销状态', command=lambda: self.sort_column('reimbursed'))
        self.tree.heading('created_at', text='创建时间', command=lambda: self.sort_column('created_at'))
        
        # 设置列宽
        self.tree.column('id', width=80)
        self.tree.column('content', width=250)
        self.tree.column('platform', width=150)
        self.tree.column('expense_type', width=100)
        self.tree.column('amount', width=120)
        self.tree.column('reimbursed', width=100)
        self.tree.column('created_at', width=180)  # 时间列宽度
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 设置交替行颜色
        self.tree.tag_configure('oddrow', background='#FFFFFF')
        self.tree.tag_configure('evenrow', background='#F0F0F0')
    
    def sort_column(self, column, is_numeric=False, is_currency=False):
        """排序指定列"""
        # 获取所有项目
        items = [(self.tree.set(item, column), item) for item in self.tree.get_children('')]
        
        # 转换排序方向
        self.sort_states[column] = not self.sort_states[column]
        reverse = self.sort_states[column]
        
        # 根据不同类型的数据进行排序
        if is_numeric:
            if is_currency:
                # 处理金额格式（去除 ¥ 和逗号）
                items.sort(key=lambda x: float(x[0].replace('¥', '').replace(',', '').strip()), reverse=reverse)
            else:
                # 处理普通数字
                items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'), reverse=reverse)
        else:
            # 字符串排序
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        
        # 重新排列项目
        for index, (val, item) in enumerate(items):
            # 更新交替行颜色
            self.tree.move(item, '', index)
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.item(item, tags=(tag,))
        
        # 更新表头显示排序方向
        for col in self.tree['columns']:
            if col == column:
                direction = '↓' if reverse else '↑'
                self.tree.heading(col, text=f"{self.get_column_title(col)} {direction}")
            else:
                self.tree.heading(col, text=self.get_column_title(col))

    def get_column_title(self, column):
        """获取列的原始标题"""
        titles = {
            'id': '编号',
            'content': '报销内容',
            'platform': '购买平台',
            'expense_type': '费用类型',
            'amount': '金额',
            'reimbursed': '报销状态',
            'created_at': '创建时间'
        }
        return titles.get(column, column)

    def insert_item(self, id, content, platform, expense_type, amount, reimbursed, created_at):
        """插入新记录"""
        reimbursed_text = "已报销" if reimbursed else "未报销"
        amount_text = f"¥ {amount:,.2f}"
        
        # 格式化时间显示
        created_at_text = created_at.strftime("%Y-%m-%d %H:%M:%S") if created_at else ""
        
        # 获取当前项目数量来决定使用哪个标签
        count = len(self.tree.get_children())
        tag = 'evenrow' if count % 2 == 0 else 'oddrow'
        
        self.tree.insert('', tk.END, 
                        values=(id, content, platform, expense_type, amount_text, reimbursed_text, created_at_text),
                        tags=(tag,))
    
    def clear_all(self):
        """清空所有记录"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        # 重置所有排序状态
        for key in self.sort_states:
            self.sort_states[key] = False
        # 重置表头文字
        for column in self.tree['columns']:
            self.tree.heading(column, text=self.get_column_title(column))
    
    def get_selected_item(self):
        """获取选中的记录"""
        selection = self.tree.selection()
        if selection:
            return self.tree.item(selection[0])
        return None 