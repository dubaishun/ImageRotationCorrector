import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageOps
import numpy as np
import cv2
from threading import Thread

class ImageRotationCorrector:
    def __init__(self, root):
        self.root = root
        self.root.title("图片旋转矫正工具")
        self.root.geometry("800x600")
        
        # 变量初始化
        self.directory = ""
        self.image_files = []
        self.current_index = 0
        self.preview_image = None
        self.correction_angle = 0
        self.auto_correct = tk.BooleanVar(value=True)
        self.process_subdirs = tk.BooleanVar(value=True)
        
        # 创建UI
        self.create_widgets()
        
    def create_widgets(self):
        # 顶部框架 - 目录选择和操作按钮
        top_frame = tk.Frame(self.root)
        top_frame.pack(pady=10, fill=tk.X)
        
        # 目录选择
        dir_btn = tk.Button(top_frame, text="选择目录", command=self.select_directory)
        dir_btn.pack(side=tk.LEFT, padx=5)
        
        self.dir_label = tk.Label(top_frame, text="未选择目录", relief=tk.SUNKEN, anchor=tk.W)
        self.dir_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 处理选项
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=5, fill=tk.X)
        
        tk.Checkbutton(options_frame, text="自动检测旋转角度", variable=self.auto_correct, 
                      command=self.toggle_auto_correct).pack(side=tk.LEFT, padx=5)
        
        tk.Checkbutton(options_frame, text="包含子目录", variable=self.process_subdirs).pack(side=tk.LEFT, padx=5)
        
        # 手动调整角度
        angle_frame = tk.Frame(self.root)
        angle_frame.pack(pady=5, fill=tk.X)
        
        tk.Label(angle_frame, text="手动调整角度:").pack(side=tk.LEFT)
        self.angle_slider = tk.Scale(angle_frame, from_=-45, to=45, orient=tk.HORIZONTAL, 
                                   command=self.manual_adjust_angle)
        self.angle_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.angle_slider.config(state=tk.DISABLED)
        
        # 图片预览区域
        preview_frame = tk.Frame(self.root)
        preview_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(preview_frame, bg='gray')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 底部按钮
        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(pady=10, fill=tk.X)
        
        tk.Button(bottom_frame, text="上一张", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="下一张", command=self.next_image).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="保存当前", command=self.save_current).pack(side=tk.LEFT, padx=5)
        tk.Button(bottom_frame, text="批量处理", command=self.batch_process).pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, mode='determinate')
        self.progress.pack(fill=tk.X, padx=10, pady=5)
        
        # 状态栏
        self.status = tk.Label(self.root, text="准备就绪", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(fill=tk.X)
    
    def select_directory(self):
        directory = filedialog.askdirectory(title="选择包含图片的目录")
        if directory:
            self.directory = directory
            self.dir_label.config(text=directory)
            self.scan_directory()
    
    def scan_directory(self):
        if not self.directory:
            return
            
        self.image_files = []
        patterns = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp')
        
        if self.process_subdirs.get():
            for root, _, files in os.walk(self.directory):
                for file in files:
                    if file.lower().endswith(patterns):
                        full_path = os.path.join(root, file)
                        # 处理中文路径问题
                        try:
                            full_path.encode('gbk').decode('gbk')
                            self.image_files.append(full_path)
                        except:
                            continue
        else:
            for file in os.listdir(self.directory):
                if file.lower().endswith(patterns):
                    full_path = os.path.join(self.directory, file)
                    try:
                        full_path.encode('gbk').decode('gbk')
                        self.image_files.append(full_path)
                    except:
                        continue
        
        if self.image_files:
            self.current_index = 0
            self.load_current_image()
            self.status.config(text=f"找到 {len(self.image_files)} 张图片")
        else:
            self.status.config(text="未找到图片文件")
    
    def load_current_image(self):
        if not self.image_files or self.current_index >= len(self.image_files):
            return
            
        try:
            self.current_image_path = self.image_files[self.current_index]
            # 使用Pillow打开图片，避免OpenCV中文路径问题
            self.original_image = Image.open(self.current_image_path)
            
            # 自动检测旋转角度
            if self.auto_correct.get():
                self.correction_angle = self.detect_rotation_angle(self.current_image_path)
                self.angle_slider.set(self.correction_angle)
            
            self.update_preview()
            self.status.config(text=f"图片 {self.current_index + 1}/{len(self.image_files)}: {os.path.basename(self.current_image_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"无法加载图片: {str(e)}")
            self.next_image()
    
    def detect_rotation_angle(self, image_path):
        try:
            # 使用Pillow读取图片，然后转换为numpy数组
            img = Image.open(image_path)
            img = np.array(img)
            
            # 如果图片是RGBA，转换为RGB
            if img.shape[2] == 4:
                img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
            elif len(img.shape) == 2:  # 灰度图
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
            
            angles = []
            if lines is not None:
                for line in lines:
                    x1, y1, x2, y2 = line[0]
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    angles.append(angle)
            
            if angles:
                # 取中位数作为旋转角度
                median_angle = np.median(angles)
                # 只考虑接近水平或垂直的角度
                if abs(median_angle) < 45:
                    return -median_angle  # 取负值进行矫正
                elif median_angle > 0:
                    return 90 - median_angle
                else:
                    return -90 - median_angle
            return 0
        except Exception as e:
            print(f"检测旋转角度时出错: {str(e)}")
            return 0
    
    def update_preview(self):
        if not hasattr(self, 'original_image'):
            return
            
        rotated_image = self.original_image.rotate(self.correction_angle, expand=True)
        
        # 调整大小以适应画布
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 700
            canvas_height = 500
        
        img_ratio = rotated_image.width / rotated_image.height
        canvas_ratio = canvas_width / canvas_height
        
        if img_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / img_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * img_ratio)
        
        preview_img = rotated_image.resize((new_width, new_height), Image.LANCZOS)
        self.preview_image = ImageTk.PhotoImage(preview_img)
        
        # 清除画布并显示图片
        self.canvas.delete("all")
        self.canvas.create_image(canvas_width//2, canvas_height//2, anchor=tk.CENTER, image=self.preview_image)
    
    def toggle_auto_correct(self):
        if self.auto_correct.get():
            self.angle_slider.config(state=tk.NORMAL)
            if hasattr(self, 'current_image_path'):
                self.correction_angle = self.detect_rotation_angle(self.current_image_path)
                self.angle_slider.set(self.correction_angle)
                self.update_preview()
        else:
            self.angle_slider.config(state=tk.DISABLED)
    
    def manual_adjust_angle(self, angle):
        try:
            self.correction_angle = float(angle)
            self.update_preview()
        except:
            pass
    
    def prev_image(self):
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def save_current(self):
        if not hasattr(self, 'current_image_path') or not hasattr(self, 'original_image'):
            return
            
        try:
            rotated_image = self.original_image.rotate(self.correction_angle, expand=True)
            
            # 获取文件扩展名
            ext = os.path.splitext(self.current_image_path)[1].lower()
            
            # 根据扩展名确定保存格式
            format_mapping = {
                '.jpg': 'JPEG',
                '.jpeg': 'JPEG',
                '.png': 'PNG',
                '.bmp': 'BMP',
                '.tiff': 'TIFF',
                '.webp': 'WEBP'
            }
            format = format_mapping.get(ext, 'JPEG')
            
            # 保存为临时文件，然后替换原文件
            temp_path = self.current_image_path + ".temp"
            rotated_image.save(temp_path, format=format, quality=95)
            
            # 替换原文件
            os.replace(temp_path, self.current_image_path)
            
            # 重新加载图片
            self.original_image = Image.open(self.current_image_path)
            self.update_preview()
            
            self.status.config(text=f"已保存: {os.path.basename(self.current_image_path)}")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def batch_process(self):
        if not self.image_files:
            messagebox.showwarning("警告", "没有可处理的图片")
            return
            
        confirm = messagebox.askyesno("确认", f"确定要批量处理 {len(self.image_files)} 张图片吗？")
        if not confirm:
            return
            
        # 在新线程中处理
        Thread(target=self._batch_process_thread, daemon=True).start()
    
    def _batch_process_thread(self):
        self.progress["maximum"] = len(self.image_files)
        
        for i, image_path in enumerate(self.image_files):
            try:
                # 更新进度
                self.root.after(0, lambda v=i+1: self.progress.config(value=v))
                self.root.after(0, lambda t=f"处理中 {i+1}/{len(self.image_files)}...": self.status.config(text=t))
                
                # 检测旋转角度
                angle = 0
                if self.auto_correct.get():
                    angle = self.detect_rotation_angle(image_path)
                
                # 旋转并保存图片
                img = Image.open(image_path)
                rotated_img = img.rotate(angle, expand=True)
                
                # 获取文件扩展名
                ext = os.path.splitext(image_path)[1].lower()
                
                # 根据扩展名确定保存格式
                format_mapping = {
                    '.jpg': 'JPEG',
                    '.jpeg': 'JPEG',
                    '.png': 'PNG',
                    '.bmp': 'BMP',
                    '.tiff': 'TIFF',
                    '.webp': 'WEBP'
                }
                format = format_mapping.get(ext, 'JPEG')
                
                # 保存为临时文件，然后替换原文件
                temp_path = image_path + ".temp"
                rotated_img.save(temp_path, format=format, quality=95)
                os.replace(temp_path, image_path)
                
            except Exception as e:
                print(f"处理 {image_path} 时出错: {str(e)}")
        
        self.root.after(0, lambda: self.progress.config(value=0))
        self.root.after(0, lambda: self.status.config(text=f"批量处理完成，共处理 {len(self.image_files)} 张图片"))
        self.root.after(0, lambda: messagebox.showinfo("完成", "批量处理完成"))

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRotationCorrector(root)
    root.mainloop()