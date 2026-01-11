import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import threading

# 尝试导入 AVIF 支持
try:
    import pillow_avif
    AVIF_SUPPORTED = True
except ImportError:
    AVIF_SUPPORTED = False


class ImageConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("图片格式转换器 (WebP / AVIF)")
        self.root.geometry("780x650")
        self.root.resizable(True, True)
        
        self.is_converting = False
        self.setup_ui()
        
    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ========== 源目录 ==========
        source_frame = ttk.LabelFrame(main_frame, text="源目录", padding="5")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_entry = ttk.Entry(source_frame)
        self.source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(source_frame, text="浏览", command=self.browse_source).pack(side=tk.RIGHT)
        
        # ========== 输出目录 ==========
        output_frame = ttk.LabelFrame(main_frame, text="输出目录", padding="5")
        output_frame.pack(fill=tk.X, pady=5)
        
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output).pack(side=tk.RIGHT)
        
        # ========== 输出格式选择 ==========
        format_frame = ttk.LabelFrame(main_frame, text="输出格式", padding="10")
        format_frame.pack(fill=tk.X, pady=5)
        
        self.format_var = tk.StringVar(value="webp")
        
        format_select_frame = ttk.Frame(format_frame)
        format_select_frame.pack(fill=tk.X)
        
        # WebP 选项
        webp_radio = ttk.Radiobutton(format_select_frame, text="WebP", 
                                      variable=self.format_var, value="webp",
                                      command=self.on_format_change)
        webp_radio.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(format_select_frame, text="(兼容性好，压缩率高)", 
                  foreground="gray").pack(side=tk.LEFT)
        
        # AVIF 选项
        avif_frame = ttk.Frame(format_select_frame)
        avif_frame.pack(side=tk.LEFT, padx=(30, 10))
        
        self.avif_radio = ttk.Radiobutton(avif_frame, text="AVIF", 
                                           variable=self.format_var, value="avif",
                                           command=self.on_format_change)
        self.avif_radio.pack(side=tk.LEFT)
        
        if AVIF_SUPPORTED:
            ttk.Label(format_select_frame, text="(压缩率更高，较新格式)", 
                      foreground="gray").pack(side=tk.LEFT)
        else:
            ttk.Label(format_select_frame, text="(未安装 pillow-avif-plugin)", 
                      foreground="red").pack(side=tk.LEFT)
            self.avif_radio.config(state=tk.DISABLED)
        
        # ========== 设置选项 ==========
        settings_frame = ttk.LabelFrame(main_frame, text="转换设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 质量设置
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(quality_frame, text="压缩质量:").pack(side=tk.LEFT)
        self.quality_var = tk.IntVar(value=85)
        self.quality_scale = ttk.Scale(quality_frame, from_=1, to=100, 
                                        variable=self.quality_var, orient=tk.HORIZONTAL)
        self.quality_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        self.quality_label = ttk.Label(quality_frame, text="85", width=4)
        self.quality_label.pack(side=tk.LEFT)
        self.quality_var.trace('w', self.update_quality_label)
        
        # 质量预设按钮
        preset_frame = ttk.Frame(settings_frame)
        preset_frame.pack(fill=tk.X, pady=5)
        ttk.Label(preset_frame, text="预设:").pack(side=tk.LEFT)
        ttk.Button(preset_frame, text="高质量(95)", width=12,
                   command=lambda: self.set_quality(95)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="均衡(85)", width=12,
                   command=lambda: self.set_quality(85)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="高压缩(75)", width=12,
                   command=lambda: self.set_quality(75)).pack(side=tk.LEFT, padx=2)
        ttk.Button(preset_frame, text="极限压缩(60)", width=12,
                   command=lambda: self.set_quality(60)).pack(side=tk.LEFT, padx=2)
        
        # 选项复选框 - 第一行
        options_frame1 = ttk.Frame(settings_frame)
        options_frame1.pack(fill=tk.X, pady=5)
        
        self.lossless_var = tk.BooleanVar(value=False)
        self.lossless_check = ttk.Checkbutton(options_frame1, text="无损压缩 (画质完全不变，但文件可能较大)", 
                                               variable=self.lossless_var, command=self.toggle_lossless)
        self.lossless_check.pack(side=tk.LEFT, padx=5)
        
        # 选项复选框 - 第二行
        options_frame2 = ttk.Frame(settings_frame)
        options_frame2.pack(fill=tk.X, pady=2)
        
        self.recursive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame2, text="包含子目录", 
                        variable=self.recursive_var).pack(side=tk.LEFT, padx=5)
        
        self.keep_structure_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame2, text="保持目录结构", 
                        variable=self.keep_structure_var).pack(side=tk.LEFT, padx=5)
        
        # 选项复选框 - 第三行
        options_frame3 = ttk.Frame(settings_frame)
        options_frame3.pack(fill=tk.X, pady=2)
        
        self.skip_larger_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame3, text="跳过变大的文件 (保留原文件)", 
                        variable=self.skip_larger_var).pack(side=tk.LEFT, padx=5)
        
        self.resize_large_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame3, text="缩小大图片 (>4K)", 
                        variable=self.resize_large_var).pack(side=tk.LEFT, padx=5)
        
        # ========== 按钮 ==========
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.convert_btn = ttk.Button(btn_frame, text="🚀 开始转换", command=self.start_conversion)
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="🗑 清空日志", command=self.clear_log).pack(side=tk.RIGHT, padx=5)
        
        # ========== 进度条 ==========
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        self.progress_label = ttk.Label(progress_frame, text="0/0", width=15)
        self.progress_label.pack(side=tk.RIGHT, padx=5)
        
        # ========== 状态和统计 ==========
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=2)
        
        self.status_label = ttk.Label(status_frame, text="就绪", foreground="green")
        self.status_label.pack(side=tk.LEFT)
        
        self.stats_label = ttk.Label(status_frame, text="", foreground="gray")
        self.stats_label.pack(side=tk.RIGHT)
        
        # ========== 日志区域 ==========
        log_frame = ttk.LabelFrame(main_frame, text="转换日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 日志文本框和滚动条
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, height=10, yscrollcommand=log_scroll.set)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # 配置日志标签颜色
        self.log_text.tag_config('success', foreground='green')
        self.log_text.tag_config('error', foreground='red')
        self.log_text.tag_config('info', foreground='blue')
        self.log_text.tag_config('copy', foreground='orange')
        self.log_text.tag_config('skip', foreground='purple')
        self.log_text.tag_config('warning', foreground='#CC6600')
    
    def on_format_change(self):
        """格式变更时的处理"""
        fmt = self.format_var.get()
        if fmt == "avif":
            self.log("已选择 AVIF 格式 - 压缩率更高，但编码速度较慢", 'info')
        else:
            self.log("已选择 WebP 格式 - 兼容性好，编码速度快", 'info')
        
    def set_quality(self, value):
        """设置质量预设"""
        if not self.lossless_var.get():
            self.quality_var.set(value)
        
    def toggle_lossless(self):
        """切换无损压缩时，禁用/启用质量滑块"""
        if self.lossless_var.get():
            self.quality_scale.config(state=tk.DISABLED)
            self.quality_label.config(foreground='gray')
        else:
            self.quality_scale.config(state=tk.NORMAL)
            self.quality_label.config(foreground='black')
        
    def update_quality_label(self, *args):
        self.quality_label.config(text=str(int(self.quality_var.get())))
        
    def browse_source(self):
        folder = filedialog.askdirectory(title="选择源目录")
        if folder:
            self.source_entry.delete(0, tk.END)
            self.source_entry.insert(0, folder)
            
    def browse_output(self):
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, folder)
            
    def log(self, message, tag=None):
        self.log_text.insert(tk.END, message + "\n", tag)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        
    def start_conversion(self):
        source = self.source_entry.get().strip()
        output = self.output_entry.get().strip()
        
        if not source:
            messagebox.showerror("错误", "请选择源目录!")
            return
        if not output:
            messagebox.showerror("错误", "请选择输出目录!")
            return
        if not os.path.exists(source):
            messagebox.showerror("错误", "源目录不存在!")
            return
        
        # 检查 AVIF 支持
        if self.format_var.get() == "avif" and not AVIF_SUPPORTED:
            messagebox.showerror("错误", "AVIF 格式需要安装 pillow-avif-plugin\n\n请运行: pip install pillow-avif-plugin")
            return
            
        self.is_converting = True
        self.convert_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        thread = threading.Thread(target=self.convert_images, args=(source, output), daemon=True)
        thread.start()
        
    def stop_conversion(self):
        self.is_converting = False
        self.status_label.config(text="正在停止...", foreground="orange")
        
    def convert_images(self, source, output):
        # 获取输出格式
        output_format = self.format_var.get()  # "webp" 或 "avif"
        format_ext = f".{output_format}"
        
        # 支持的图片格式
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.tif', '.ico', '.ppm', '.pgm', '.pbm'}
        target_formats = {'.webp', '.avif'}
        
        # 创建输出目录
        if not os.path.exists(output):
            os.makedirs(output)
            
        # 收集所有图片文件
        files = []
        if self.recursive_var.get():
            for root_dir, dirs, filenames in os.walk(source):
                for filename in filenames:
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in supported_formats or ext in target_formats:
                        full_path = os.path.join(root_dir, filename)
                        rel_path = os.path.relpath(root_dir, source)
                        files.append((full_path, filename, rel_path))
        else:
            for filename in os.listdir(source):
                filepath = os.path.join(source, filename)
                if os.path.isfile(filepath):
                    ext = os.path.splitext(filename)[1].lower()
                    if ext in supported_formats or ext in target_formats:
                        files.append((filepath, filename, '.'))
                        
        total = len(files)
        if total == 0:
            self.log("未找到任何图片文件!", 'error')
            self.reset_ui()
            return
            
        self.progress['maximum'] = total
        self.progress['value'] = 0
        self.log(f"找到 {total} 个图片文件，开始转换为 {output_format.upper()}...", 'info')
        
        converted_count = 0
        copied_count = 0
        skipped_count = 0
        error_count = 0
        total_original_size = 0
        total_new_size = 0
        
        quality = int(self.quality_var.get())
        lossless = self.lossless_var.get()
        keep_structure = self.keep_structure_var.get()
        skip_larger = self.skip_larger_var.get()
        resize_large = self.resize_large_var.get()
        
        for i, (filepath, filename, rel_path) in enumerate(files):
            if not self.is_converting:
                self.log("转换已停止!", 'info')
                break
                
            name, ext = os.path.splitext(filename)
            original_size = os.path.getsize(filepath)
            
            # 确定输出路径
            if keep_structure and rel_path != '.':
                out_dir = os.path.join(output, rel_path)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
            else:
                out_dir = output
                
            try:
                # 如果已经是目标格式，直接复制
                if ext.lower() == format_ext:
                    output_path = os.path.join(out_dir, filename)
                    output_path = self.get_unique_path(output_path)
                    shutil.copy2(filepath, output_path)
                    copied_count += 1
                    total_original_size += original_size
                    total_new_size += original_size
                    self.log(f"[复制] {filename} (已是{output_format.upper()}格式)", 'copy')
                    
                # 如果是另一种目标格式，也复制到输出目录
                elif ext.lower() in target_formats:
                    output_path = os.path.join(out_dir, filename)
                    output_path = self.get_unique_path(output_path)
                    shutil.copy2(filepath, output_path)
                    copied_count += 1
                    total_original_size += original_size
                    total_new_size += original_size
                    self.log(f"[复制] {filename}", 'copy')
                    
                else:
                    # 转换图片
                    img = Image.open(filepath)
                    
                    # 缩小大图片
                    if resize_large:
                        max_size = 3840  # 4K
                        if img.width > max_size or img.height > max_size:
                            ratio = min(max_size / img.width, max_size / img.height)
                            new_size = (int(img.width * ratio), int(img.height * ratio))
                            img = img.resize(new_size, Image.Resampling.LANCZOS)
                            self.log(f"  ↳ 缩小: {img.width}x{img.height}", 'info')
                    
                    # 处理不同的图像模式
                    if img.mode == 'P':
                        if 'transparency' in img.info:
                            img = img.convert('RGBA')
                        else:
                            img = img.convert('RGB')
                    elif img.mode == 'LA':
                        img = img.convert('RGBA')
                    elif img.mode not in ('RGB', 'RGBA'):
                        img = img.convert('RGB')
                    
                    # 如果没有透明通道，转为RGB可以更好压缩
                    if img.mode == 'RGBA':
                        extrema = img.getextrema()
                        if len(extrema) >= 4 and extrema[3][0] == 255:
                            img = img.convert('RGB')
                    
                    output_path = os.path.join(out_dir, name + format_ext)
                    output_path = self.get_unique_path(output_path)
                    
                    # 根据格式保存
                    if output_format == "webp":
                        if lossless:
                            img.save(output_path, 'WEBP', lossless=True, quality=100, method=6)
                        else:
                            img.save(output_path, 'WEBP', quality=quality, method=6)
                    else:  # AVIF
                        if lossless:
                            # AVIF 无损
                            img.save(output_path, 'AVIF', quality=100, speed=6)
                        else:
                            # AVIF 有损 - speed 越低压缩越好但越慢
                            img.save(output_path, 'AVIF', quality=quality, speed=6)
                    
                    new_size = os.path.getsize(output_path)
                    
                    # 检查是否变大了
                    if skip_larger and new_size >= original_size:
                        os.remove(output_path)
                        
                        # 复制原文件
                        original_output = os.path.join(out_dir, filename)
                        original_output = self.get_unique_path(original_output)
                        shutil.copy2(filepath, original_output)
                        
                        skipped_count += 1
                        total_original_size += original_size
                        total_new_size += original_size
                        self.log(f"[跳过] {filename} ({output_format.upper()}更大: {self.format_size(original_size)} → {self.format_size(new_size)})", 'skip')
                    else:
                        ratio = (1 - new_size / original_size) * 100
                        converted_count += 1
                        total_original_size += original_size
                        total_new_size += new_size
                        
                        if ratio >= 0:
                            self.log(f"[转换] {filename} → {os.path.basename(output_path)} "
                                    f"({self.format_size(original_size)} → {self.format_size(new_size)}, "
                                    f"节省 {ratio:.1f}%)", 'success')
                        else:
                            self.log(f"[转换] {filename} → {os.path.basename(output_path)} "
                                    f"({self.format_size(original_size)} → {self.format_size(new_size)}, "
                                    f"增大 {-ratio:.1f}%)", 'warning')
                    
                    img.close()
                    
            except Exception as e:
                error_count += 1
                self.log(f"[错误] {filename}: {str(e)}", 'error')
                
            # 更新进度
            self.progress['value'] = i + 1
            self.progress_label.config(text=f"{i + 1}/{total}")
            self.status_label.config(text=f"处理中: {filename}", foreground="blue")
            
            # 更新统计
            if total_original_size > 0:
                overall_ratio = (1 - total_new_size / total_original_size) * 100
                self.stats_label.config(
                    text=f"总计: {self.format_size(total_original_size)} → {self.format_size(total_new_size)} (节省 {overall_ratio:.1f}%)"
                )
            
            self.root.update_idletasks()
            
        # 完成
        self.log("-" * 60, 'info')
        
        summary = f"转换完成! 格式: {output_format.upper()}\n  转换: {converted_count} | 复制: {copied_count} | 跳过: {skipped_count} | 错误: {error_count}"
        if total_original_size > 0:
            overall_ratio = (1 - total_new_size / total_original_size) * 100
            summary += f"\n  总大小: {self.format_size(total_original_size)} → {self.format_size(total_new_size)} (节省 {overall_ratio:.1f}%)"
        self.log(summary, 'info')
        
        self.reset_ui()
        
        if self.is_converting:
            msg = (f"转换完成! 格式: {output_format.upper()}\n\n"
                   f"✅ 转换: {converted_count} 个文件\n"
                   f"📋 复制: {copied_count} 个文件\n"
                   f"⏭ 跳过: {skipped_count} 个文件 (转换后更大)\n"
                   f"❌ 错误: {error_count} 个文件\n\n")
            if total_original_size > 0:
                overall_ratio = (1 - total_new_size / total_original_size) * 100
                saved = total_original_size - total_new_size
                msg += f"💾 总节省: {self.format_size(saved)} ({overall_ratio:.1f}%)"
            messagebox.showinfo("完成", msg)
        
    def get_unique_path(self, path):
        """获取唯一的文件路径，避免覆盖"""
        if not os.path.exists(path):
            return path
            
        base, ext = os.path.splitext(path)
        counter = 1
        while os.path.exists(f"{base}_{counter}{ext}"):
            counter += 1
        return f"{base}_{counter}{ext}"
        
    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
        
    def reset_ui(self):
        self.is_converting = False
        self.convert_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="就绪", foreground="green")


def main():
    root = tk.Tk()
    app = ImageConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()