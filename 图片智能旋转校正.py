import base64
import urllib
import requests
from PIL import Image
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from tkinter import scrolledtext
import glob

# 自动安装缺失库
def install_package(package):
    try:
        __import__(package)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 尝试导入所需库
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    install_package('tkinterdnd2')
    try:
        from tkinterdnd2 import TkinterDnD, DND_FILES
    except ImportError:
        messagebox.showerror("错误", "请手动安装 tkinterdnd2: pip install tkinterdnd2")
        sys.exit()

API_KEY = "XUGkP99QPfUJOYfMWqy8JjAB"
SECRET_KEY = "fOVu2rdNi4DfJkITY4fCSoP50DDPX5AB"

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片智能旋转校正")
        self.center_window(600, 500)
        
        # 创建GUI元素
        self.create_widgets()
        
    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def create_widgets(self):
        # 目录选择区域
        frame_select = tk.Frame(self.root)
        frame_select.pack(pady=10)
        
        self.dir_path = tk.StringVar()
        dir_entry = tk.Entry(frame_select, textvariable=self.dir_path, width=50)
        dir_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = tk.Button(frame_select, text="选择目录", command=self.browse_directory)
        browse_btn.pack(side=tk.LEFT)
        
        # 选项区域
        frame_options = tk.LabelFrame(self.root, text="选项", padx=10, pady=10)
        frame_options.pack(pady=10, fill=tk.X, padx=20)
        
        self.detect_direction = tk.BooleanVar(value=True)
        direction_cb = tk.Checkbutton(frame_options, text="检测图片朝向", variable=self.detect_direction)
        direction_cb.pack(anchor=tk.W)
        
        # 操作按钮区域
        frame_buttons = tk.Frame(self.root)
        frame_buttons.pack(pady=20)
        
        self.process_btn = tk.Button(frame_buttons, text="批量校正", command=self.batch_correct)
        self.process_btn.pack(side=tk.LEFT, padx=10)
        
        # 进度显示区域
        frame_progress = tk.Frame(self.root)
        frame_progress.pack(fill=tk.X, padx=20, pady=5)
        
        self.progress_label = tk.Label(frame_progress, text="准备就绪")
        self.progress_label.pack(side=tk.LEFT)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(frame_progress, orient=tk.HORIZONTAL, 
                                          length=300, mode='determinate', variable=self.progress_var)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 结果显示区域
        frame_result = tk.LabelFrame(self.root, text="处理结果", padx=10, pady=10)
        frame_result.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        self.result_text = scrolledtext.ScrolledText(frame_result, height=10, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加底部版权信息
        self.copyright_frame = tk.Frame(self.root, bg="yellow")
        self.copyright_frame.pack(fill="x", side="bottom", pady=5)
        
        copyright_text = "关注速光网络软件开发，抖音号：dubaishun12 私信博主，免费获取注册码"
        self.copyright_label = tk.Label(
            self.copyright_frame, 
            text=copyright_text,
            bg="yellow",
            font=("微软雅黑", 10)
        )
        self.copyright_label.pack(expand=True)
    
    def browse_directory(self):
        dir_path = filedialog.askdirectory(title='选择图片目录')
        if dir_path:
            self.dir_path.set(dir_path)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"已选择目录: {dir_path}\n")
    
    def update_progress(self, value, message=None):
        self.progress_var.set(value)
        if message:
            self.progress_label.config(text=message)
        self.root.update_idletasks()
    
    def get_access_token(self):
        """获取百度OCR的Access Token"""
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
        
        try:
            response = requests.post(url, params=params)
            return str(response.json().get("access_token"))
        except Exception as e:
            messagebox.showerror("错误", f"获取Access Token失败: {str(e)}")
            return None
    
    def get_file_content_as_base64(self, path, urlencoded=False):
        """获取文件base64编码"""
        try:
            with open(path, "rb") as f:
                content = base64.b64encode(f.read()).decode("utf8")
                if urlencoded:
                    content = urllib.parse.quote_plus(content)
                return content
        except Exception as e:
            self.log_result(f"读取文件失败: {str(e)}")
            return None
    
    def log_result(self, message):
        self.result_text.insert(tk.END, message + "\n")
        self.result_text.see(tk.END)
        self.root.update_idletasks()
    
    def detect_image_rotation(self, image_path, access_token):
        """检测单张图片的旋转方向"""
        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token=" + access_token
        image_base64 = self.get_file_content_as_base64(image_path, True)
        if not image_base64:
            return None
            
        payload = f"image={image_base64}&detect_direction={str(self.detect_direction.get()).lower()}"
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
        
        try:
            response = requests.post(url, headers=headers, data=payload.encode("utf-8"))
            result = response.json()
            
            if 'error_code' in result:
                self.log_result(f"检测失败({os.path.basename(image_path)}): {result['error_msg']}")
                return None
                
            return result.get('direction', -1)
        except Exception as e:
            self.log_result(f"检测过程中出错({os.path.basename(image_path)}): {str(e)}")
            return None
    
    def correct_image_rotation(self, image_path, direction):
        """校正单张图片旋转"""
        if direction == -1:
            self.log_result(f"图片无需校正: {os.path.basename(image_path)}")
            return False
            
        # 计算需要旋转的角度（根据API文档）
        rotation_map = {
            -1: 0,    # 未定义，不旋转
            0: 0,     # 正向，不旋转
            1: 270,   # 逆时针90度 = 顺时针270度
            2: 180,   # 逆时针180度 = 顺时针180度
            3: 90     # 逆时针270度 = 顺时针90度
        }
        
        angle = rotation_map.get(direction, 0)
        if angle == 0:
            return False
            
        try:
            # 获取原始文件扩展名
            file_ext = os.path.splitext(image_path)[1].lower()
            # 创建带有原始扩展名的临时文件
            temp_path = image_path + "_temp" + file_ext
            
            with Image.open(image_path) as img:
                rotated_img = img.rotate(angle, expand=True)
                rotated_img.save(temp_path, format=img.format)
            
            # 删除原文件并将临时文件重命名为原文件名
            os.remove(image_path)
            os.rename(temp_path, image_path)
            
            self.log_result(f"已校正: {os.path.basename(image_path)}")
            return True
        except Exception as e:
            # 如果出错，尝试删除临时文件
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            self.log_result(f"校正失败({os.path.basename(image_path)}): {str(e)}")
            return False
    
    def find_image_files(self, directory):
        """递归查找目录中的所有图片文件"""
        supported_ext = ('.jpg', '.jpeg', '.png', '.bmp')
        image_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if os.path.splitext(file)[1].lower() in supported_ext:
                    image_files.append(os.path.join(root, file))
        
        return image_files
    
    def batch_correct(self):
        """批量校正目录中的图片（包括子目录）"""
        if not self.dir_path.get():
            messagebox.showwarning("警告", "请先选择目录")
            return
            
        dir_path = self.dir_path.get()
        
        self.process_btn.config(state=tk.DISABLED)
        self.result_text.delete(1.0, tk.END)
        self.log_result(f"开始扫描目录: {dir_path}")
        self.update_progress(5, "正在扫描图片文件...")
        
        # 查找所有图片文件（包括子目录）
        image_files = self.find_image_files(dir_path)
        
        if not image_files:
            messagebox.showwarning("警告", "目录中没有支持的图片文件")
            self.process_btn.config(state=tk.NORMAL)
            return
            
        self.log_result(f"找到 {len(image_files)} 张图片需要处理")
        
        # 获取Access Token
        self.update_progress(10, "正在获取Access Token...")
        access_token = self.get_access_token()
        if not access_token:
            self.process_btn.config(state=tk.NORMAL)
            return
            
        total = len(image_files)
        corrected_count = 0
        processed_count = 0
        
        for i, image_path in enumerate(image_files):
            relative_path = os.path.relpath(image_path, dir_path)
            self.update_progress(10 + i * 80 // total, f"正在处理: {relative_path} ({i+1}/{total})")
            
            # 检测图片旋转
            direction = self.detect_image_rotation(image_path, access_token)
            if direction is None:
                continue
                
            # 校正图片
            if self.correct_image_rotation(image_path, direction):
                corrected_count += 1
                
            processed_count += 1
            self.update_progress(10 + (i + 1) * 80 // total)
        
        self.update_progress(100, "处理完成")
        self.log_result("\n处理结果:")
        self.log_result(f"已处理图片: {processed_count}/{total}")
        self.log_result(f"已校正图片: {corrected_count}")
        messagebox.showinfo("完成", "批量处理完成")
        self.process_btn.config(state=tk.NORMAL)

def main():
    try:
        # Windows下设置DPI感知
        if os.name == 'nt':
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
            
        root = tk.Tk()
        app = OCRApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("错误", f"程序启动失败: {str(e)}")

if __name__ == '__main__':
    main()