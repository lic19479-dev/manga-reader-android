# 构建触发
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.utils import platform
from kivy.clock import Clock
import os


class MangaReader(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 10
        self.spacing = 10

        # 适配OPPO A57屏幕
        if platform != 'android':  # 只在PC测试时调整窗口大小
            Window.size = (360, 640)

        self.current_page = 0
        self.image_files = []
        self.folder_path = ""

        # 在__init__中定义所有实例变量
        self.image_display = None
        self.open_btn = None
        self.prev_btn = None
        self.next_btn = None
        self.info_label = None
        self.popup = None

        self.create_ui()

        # 延迟请求权限
        if platform == 'android':
            Clock.schedule_once(self.request_android_permissions, 1)

    def create_ui(self):
        """创建针对OPPO A57优化的界面"""
        # 标题
        title_label = Label(
            text='OPPO A57 漫画阅读器',
            size_hint_y=0.08,
            font_size='18sp',
            color=[1, 1, 1, 1],
            bold=True
        )

        # 图片显示区域 - 使用新的属性名
        self.image_display = Image(
            size_hint_y=0.7,
            fit_mode='contain'  # 替换 allow_stretch 和 keep_ratio
        )

        # 控制区域
        controls = BoxLayout(
            size_hint_y=0.12,
            spacing=10
        )

        self.open_btn = Button(
            text='打开文件夹',
            background_color=[0.2, 0.6, 0.8, 1],
            font_size='14sp'
        )
        self.open_btn.bind(on_press=self.open_folder_dialog)

        self.prev_btn = Button(
            text='上一页',
            background_color=[0.3, 0.7, 0.3, 1],
            font_size='14sp'
        )
        self.prev_btn.bind(on_press=self.prev_page)

        self.next_btn = Button(
            text='下一页',
            background_color=[0.3, 0.7, 0.3, 1],
            font_size='14sp'
        )
        self.next_btn.bind(on_press=self.next_page)

        controls.add_widget(self.open_btn)
        controls.add_widget(self.prev_btn)
        controls.add_widget(self.next_btn)

        # 页面信息
        self.info_label = Label(
            text='请点击"打开文件夹"选择漫画',
            size_hint_y=0.1,
            font_size='12sp',
            color=[1, 1, 1, 1]
        )

        self.add_widget(title_label)
        self.add_widget(self.image_display)
        self.add_widget(controls)
        self.add_widget(self.info_label)

    def request_android_permissions(self, dt=None):
        """请求Android存储权限"""
        try:
            if platform == 'android':
                # 动态导入Android模块
                from android.permissions import Permission, request_permissions

                permissions = [
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE
                ]
                request_permissions(permissions, self.permission_callback)
        except ImportError:
            # 在非Android平台上忽略导入错误
            self.info_label.text = "PC模式：可以直接打开文件夹"

    def permission_callback(self, permissions, grants):
        """权限请求回调"""
        if all(grants):
            self.info_label.text = "权限获取成功，可以打开文件夹了"
        else:
            self.info_label.text = "需要存储权限才能读取漫画文件"

    def get_android_storage_path(self):
        """获取Android存储路径"""
        try:
            if platform == 'android':
                from android.storage import primary_external_storage_path
                base_path = primary_external_storage_path()
                return base_path
        except ImportError:
            # 在非Android平台上使用备用路径
            pass

        # PC测试时使用当前目录或用户目录
        return os.path.expanduser("~")

    def open_folder_dialog(self, instance):
        """显示文件夹选择对话框"""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)

        # 常用路径按钮
        paths_layout = BoxLayout(size_hint_y=0.3, spacing=5)

        common_folders = [
            ('DCIM', '/DCIM'),
            ('Download', '/Download'),
            ('Pictures', '/Pictures'),
            ('Documents', '/Documents'),
            ('漫画', '/漫画'),
            ('Manga', '/Manga')
        ]

        for name, path in common_folders:
            btn = Button(text=name, size_hint_x=0.5, font_size='12sp')
            btn.bind(on_press=lambda x, p=path: self.select_folder(p))
            paths_layout.add_widget(btn)

        # 手动选择按钮
        manual_btn = Button(
            text='手动选择文件夹',
            size_hint_y=0.2,
            background_color=[0.8, 0.5, 0.2, 1]
        )
        manual_btn.bind(on_press=self.manual_select_folder)

        content.add_widget(Label(text='选择漫画文件夹:', size_hint_y=0.2))
        content.add_widget(paths_layout)
        content.add_widget(manual_btn)

        self.popup = Popup(
            title='OPPO A57 - 选择文件夹',
            content=content,
            size_hint=(0.9, 0.6)
        )
        self.popup.open()

    def select_folder(self, relative_path):
        """选择预设文件夹"""
        if self.popup:
            self.popup.dismiss()
        base_path = self.get_android_storage_path()
        full_path = base_path + relative_path
        self.folder_path = full_path
        self.info_label.text = f'正在扫描: {full_path}'
        # 直接加载，避免线程问题
        self.load_images_from_folder(full_path)

    def manual_select_folder(self, instance):
        """手动选择文件夹（简化版）"""
        if self.popup:
            self.popup.dismiss()

        # 提供测试文件夹选项（PC测试用）
        content = BoxLayout(orientation='vertical', spacing=10)

        test_folders = [
            ('测试文件夹1 (当前目录)', '.'),
            ('测试文件夹2 (用户目录)', '~'),
            ('Pictures', '~/Pictures'),
            ('Downloads', '~/Downloads')
        ]

        for name, path in test_folders:
            btn = Button(text=name, size_hint_y=0.2)
            expanded_path = os.path.expanduser(path)
            btn.bind(on_press=lambda x, p=expanded_path: self.select_manual_folder(p))
            content.add_widget(btn)

        popup = Popup(
            title='选择测试文件夹 (PC模式)',
            content=content,
            size_hint=(0.8, 0.6)
        )
        popup.open()

    def select_manual_folder(self, folder_path):
        """选择手动找到的文件夹"""
        self.folder_path = folder_path
        self.info_label.text = f'正在扫描: {folder_path}'
        self.load_images_from_folder(folder_path)

    def count_images_in_folder(self, folder_path):
        """计算文件夹中的图片数量"""
        try:
            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
            count = 0
            for file in os.listdir(folder_path):
                if file.lower().endswith(image_extensions):
                    count += 1
            return count
        except:
            return 0

    def load_images_from_folder(self, folder_path):
        """从文件夹加载图片"""
        try:
            expanded_path = os.path.expanduser(folder_path)
            self.info_label.text = f'正在扫描: {expanded_path}'

            if not os.path.exists(expanded_path):
                self.info_label.text = f'文件夹不存在: {expanded_path}'
                return

            image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')
            image_files = []

            # 搜索图片文件
            for file in os.listdir(expanded_path):
                if file.lower().endswith(image_extensions):
                    full_path = os.path.join(expanded_path, file)
                    image_files.append(full_path)

            # 按文件名排序
            image_files.sort()

            if image_files:
                self.image_files = image_files
                self.current_page = 0
                self.update_display()
                folder_name = os.path.basename(expanded_path)
                self.info_label.text = f'找到 {len(image_files)} 张图片，第1页 - {folder_name}'
            else:
                self.info_label.text = f'在 {expanded_path} 中未找到图片文件'
                self.image_files = []

        except Exception as e:
            self.info_label.text = f'扫描出错: {str(e)}'

    def update_display(self):
        """更新显示"""
        if self.image_files and 0 <= self.current_page < len(self.image_files):
            try:
                self.image_display.source = self.image_files[self.current_page]
                page_info = f'第{self.current_page + 1}页/共{len(self.image_files)}页'
                if hasattr(self, 'folder_path') and self.folder_path:
                    folder_name = os.path.basename(self.folder_path)
                    page_info += f' - {folder_name}'
                self.info_label.text = page_info
            except Exception as e:
                self.info_label.text = f'加载图片失败: {str(e)}'

    def next_page(self, instance):
        """下一页"""
        if self.image_files and self.current_page < len(self.image_files) - 1:
            self.current_page += 1
            self.update_display()

    def prev_page(self, instance):
        """上一页"""
        if self.image_files and self.current_page > 0:
            self.current_page -= 1
            self.update_display()


class MangaReaderApp(App):
    def build(self):
        self.title = "OPPO A57 漫画阅读器"
        # 设置窗口背景色
        Window.clearcolor = (0.1, 0.1, 0.1, 1)
        return MangaReader()


if __name__ == '__main__':
    MangaReaderApp().run()
