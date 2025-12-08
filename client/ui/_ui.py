
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from tkutils import TkLoop
from service import Service

from ._stray import StrayIcon
from ._autostart import setup_start_on_boot, remove_start_on_boot

import pyperclip


class ConfigApp(ttk.Frame):
    """
    一个基于tkinter构建的配置界面类。
    它包含了多个输入字段、复选框和按钮，并能响应窗口缩放。
    """
    def __init__(self, loop: TkLoop, service: Service, main_script: str):
        super().__init__(loop.tk, padding="10")
        self.loop = loop
        self.master: tk.Tk = loop.tk # type: ignore
        self.service = service
        self.main_script = main_script

        self.loop.schedule(lambda emit: self.service.mainloop(), separate_thread=True)

        self.master.protocol('WM_DELETE_WINDOW', self._close_window)
        self.icon = StrayIcon(loop, "showup", "exit")
        self.icon.start()
        self.loop.register_handler("exit", lambda ge: self._exit_app())
        self.loop.register_handler("showup", lambda ge: self._show_window())
        self.loop.register_handler("copy_ip", lambda ge: self._copy_ip())

        self.master.title("DyNamicS Win GUI")
        self.master.geometry("500x600") # 设置一个初始大小
        self.master.minsize(450, 550)   # 设置一个最小大小

        # 使主框架能够随窗口缩放
        self.grid(row=0, column=0, sticky="nsew")
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)

        # --- 创建Tkinter变量 ---
        self._create_variables()

        # 加载已保存配置文件
        self._load_config()

        # --- 创建UI小部件 ---
        self._create_widgets()

        # --- 初始化UI状态 ---
        self._toggle_ssid_entry() # 根据复选框初始状态设置SSID输入框

    def _create_variables(self):
        """创建所有与UI控件绑定的Tkinter变量"""
        self.api_url_var = tk.StringVar(value="https://api.example.com/v1")
        self.api_token_var = tk.StringVar()
        
        self.use_wifi_var = tk.BooleanVar(value=True)
        self.target_ssid_var = tk.StringVar(value="SUDA_WIFI")
        self.wifi_password = tk.StringVar(value="password")
        
        self.suda_config_var = tk.StringVar()
        self.scan_interval_var = tk.DoubleVar(value=60)
        self.start_on_boot_var = tk.BooleanVar(value=False)
        
        self.isp_var = tk.StringVar()
        self.account_var = tk.StringVar()
        self.password_var = tk.StringVar()

    def _create_widgets(self):
        """创建并布局所有UI小部件"""
        # 配置主框架的列权重，让第二列（输入框）可以伸展
        self.grid_columnconfigure(0, weight=1)

        # --- 1. API 设置 ---
        api_frame = ttk.LabelFrame(self, text="DyNamicS API", padding="10")
        api_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        api_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(api_frame, text="API Url:").grid(row=0, column=0, sticky="w", pady=2)
        api_url_entry = ttk.Entry(api_frame, textvariable=self.api_url_var)
        api_url_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(api_frame, text="API Token:").grid(row=1, column=0, sticky="w", pady=2)
        api_token_entry = ttk.Entry(api_frame, textvariable=self.api_token_var)
        api_token_entry.grid(row=1, column=1, sticky="ew", pady=2)

        # --- 2. 网络设置 ---
        wifi_frame = ttk.LabelFrame(self, text="WiFi", padding="10")
        wifi_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        wifi_frame.grid_columnconfigure(1, weight=1)

        use_wifi_check = ttk.Checkbutton(
            wifi_frame, 
            text="Use WiFi", 
            variable=self.use_wifi_var,
            command=self._toggle_ssid_entry
        )
        use_wifi_check.grid(row=0, column=0, sticky="w", pady=2)

        ttk.Label(wifi_frame, text="Target SSID:").grid(row=1, column=0, sticky="w", pady=2)
        self.ssid_entry = ttk.Entry(wifi_frame, textvariable=self.target_ssid_var)
        self.ssid_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(wifi_frame, text="WiFi Password:").grid(row=2, column=0, sticky="w", pady=2)
        self.wifi_password_entry = ttk.Entry(wifi_frame, textvariable=self.wifi_password, show='*')
        self.wifi_password_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # --- 3. 应用配置 ---
        app_frame = ttk.LabelFrame(self, text="Service", padding="10")
        app_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        app_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(app_frame, text="Suda Config:").grid(row=0, column=0, sticky="w", pady=2)
        suda_config_entry = ttk.Entry(app_frame, textvariable=self.suda_config_var)
        suda_config_entry.grid(row=0, column=1, sticky="ew", pady=2)
        suda_config_button = ttk.Button(app_frame, text="Select...", command=self._select_suda_config)
        suda_config_button.grid(row=0, column=2, sticky="e", padx=(5, 0), pady=2)

        ttk.Label(app_frame, text="Scan Interval (s):").grid(row=1, column=0, sticky="w", pady=2)
        scan_interval_entry = ttk.Entry(app_frame, textvariable=self.scan_interval_var)
        scan_interval_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=2)
        
        start_on_boot_check = ttk.Checkbutton(app_frame, text="Start on Boot", variable=self.start_on_boot_var, command=self._toggle_start_on_boot)
        start_on_boot_check.grid(row=2, column=0, sticky="w", pady=2)

        # --- 4. ISP 认证 ---
        isp_frame = ttk.LabelFrame(self, text="Login", padding="10")
        isp_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        isp_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(isp_frame, text="ISP:").grid(row=0, column=0, sticky="w", pady=2)
        isp_entry = ttk.Entry(isp_frame, textvariable=self.isp_var)
        isp_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(isp_frame, text="Account:").grid(row=1, column=0, sticky="w", pady=2)
        account_entry = ttk.Entry(isp_frame, textvariable=self.account_var)
        account_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(isp_frame, text="Password:").grid(row=2, column=0, sticky="w", pady=2)
        password_entry = ttk.Entry(isp_frame, textvariable=self.password_var, show="*")
        password_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # --- 5. 操作按钮 ---
        button_frame = ttk.Frame(self, padding=(0, 10))
        button_frame.grid(row=4, column=0, sticky="se")
        # 让按钮所在的行在垂直方向上可以扩展，从而将按钮推到底部
        self.grid_rowconfigure(4, weight=1) 
        # 让按钮框在自己的单元格里靠右下对齐
        
        save_button = ttk.Button(button_frame, text="Save", command=self._save_config)
        save_button.pack(side="left", padx=(0, 5))

        exit_button = ttk.Button(button_frame, text="Stop & Exit", command=self._exit_app)
        exit_button.pack(side="left")


    def _show_window(self):
        self.master.deiconify()

    def _close_window(self):
        self.master.withdraw()

    def _copy_ip(self):
        current_ip = self.service.client.current_ip
        pyperclip.copy(current_ip)
        messagebox.showinfo("DyNamicS", f"IP copied: {current_ip}")


    def _load_config(self):
        cfg = self.service.config.dump_dict()
        self.api_url_var.set(cfg.get("api_url", ""))
        self.api_token_var.set(cfg.get("api_token", ""))
        self.use_wifi_var.set(cfg.get("use_wifi", False))
        self.target_ssid_var.set(cfg.get("target_ssid", ""))
        self.wifi_password.set(cfg.get("wifi_password", ""))
        self.suda_config_var.set(cfg.get("suda_config_path", ""))
        self.scan_interval_var.set(cfg.get("scan_interval", 60))
        self.start_on_boot_var.set(cfg.get("start_on_boot", False))
        self.isp_var.set(cfg.get("isp", ""))
        self.account_var.set(cfg.get("account", ""))
        self.password_var.set(cfg.get("password", ""))
    
    def _save_config(self):
        """收集所有配置并执行保存操作（此处为打印和弹窗）"""
        config_data = {
            "api_url": self.api_url_var.get(),
            "api_token": self.api_token_var.get(),
            "use_wifi": self.use_wifi_var.get(),
            "target_ssid": self.target_ssid_var.get(),
            "wifi_password": self.wifi_password.get(),
            "suda_config_path": self.suda_config_var.get(),
            "scan_interval": self.scan_interval_var.get(),
            "start_on_boot": self.start_on_boot_var.get(),
            "isp": self.isp_var.get(),
            "account": self.account_var.get(),
            "password": self.password_var.get()
        }
        
        self.service.update_config(config_data)
        self.service.save_config()
        
        # 显示一个消息框
        messagebox.showinfo("Success", "Configuration has been saved successfully!")

    def _exit_app(self):
        self.icon.stop()
        self.icon.join()
        self.service.stop()
        self.master.destroy()


    def _toggle_ssid_entry(self):
        """根据 'Use WiFi' 复选框的状态启用或禁用 SSID 输入框"""
        if self.use_wifi_var.get():
            self.ssid_entry.config(state="normal")
            self.wifi_password_entry.config(state="normal")
        else:
            self.ssid_entry.config(state="disabled")
            self.wifi_password_entry.config(state="disabled")

    def _toggle_start_on_boot(self):
        if self.start_on_boot_var.get():
            res = setup_start_on_boot(self.main_script)
            notice = (
                "Start on boot successfully enabled." if res else
                "Failed to enable start on boot."
            )
        else:
            res = remove_start_on_boot()
            notice = (
                "Start on boot successfully disabled." if res else
                "Failed to disable start on boot."
            )
        messagebox.showinfo("DyNamicS", notice)


    def _select_suda_config(self):
        """打开文件对话框选择 Suda 配置文件"""
        filepath = filedialog.askopenfilename(
            title="Select Suda Config File",
            filetypes=(("Config files", "*.json"), ("All files", "*.*"))
        )
        if filepath:
            self.suda_config_var.set(filepath)
