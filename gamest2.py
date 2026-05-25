import pygame
import sys
import random
import math
import os

pygame.init()
# Khởi tạo Pygame
pygame.mixer.init()

# =========================================================================
# CẤU HÌNH HỆ THỐNG ÂM THANH TOÀN CỤC
# =========================================================================
sound_volume = 0.5  # Âm thanh nền (Music)
sfx_volume = 0.7    # Tiếng súng/Hiệu ứng (SFX)
is_dragging_bg = False
is_dragging_sfx = False

# Load nhạc nền
try:
    pygame.mixer.music.load("Quay-màn-hình-2026-05-19-001548.wav")
    pygame.mixer.music.set_volume(sound_volume)
    pygame.mixer.music.play(-1)  # loop vô hạn
except:
    print("Không tìm thấy file nhạc nền, tiếp tục game không có nhạc")

# Khởi tạo các biến âm thanh là None trước phòng hờ lỗi
sound_pistol = None
sound_ak47 = None
sound_ump = None
sound_shotgun = None

try:
    sound_pistol  = pygame.mixer.Sound("pistol.wav")
    sound_ak47    = pygame.mixer.Sound("ak47.wav")
    sound_ump     = pygame.mixer.Sound("uzi.wav")
    sound_shotgun = pygame.mixer.Sound("shotgun.wav")

    # Áp dụng cấu hình sfx_volume cho các hiệu ứng tiếng súng
    sound_pistol.set_volume(sfx_volume)
    sound_ak47.set_volume(sfx_volume)
    sound_ump.set_volume(sfx_volume)
    sound_shotgun.set_volume(sfx_volume)
    print("Tải âm thanh súng thành công!")
except pygame.error as e:
    print(f"CẢNH BÁO: Không thể tải file âm thanh súng. Chi tiết lỗi: {e}")
    print("Trò chơi sẽ tiếp tục chạy mà không có tiếng súng để tránh crash.")

# Cấu hình màn hình hiển thị
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sinh Tồn Thành Phố Nhiễm Độc")

clock = pygame.time.Clock()
FPS = 60

# =========================================================================
# CẤU HÌNH FONT CHỮ - HỖ TRỢ TIẾNG VIỆT
# =========================================================================
def get_font(font_name, size, bold=False, italic=False):
    """Tạo font chữ an toàn, fallback nếu font không có"""
    try:
        font = pygame.font.SysFont(font_name, size, bold, italic)
        test_surface = font.render("áàảãạăắằẳẵặâấầẩẫậ", True, (255,255,255))
        return font
    except:
        pass
    
    fallback_fonts = [
        "Arial", "Tahoma", "Segoe UI", "Microsoft Sans Serif", 
        "DejaVu Sans", "FreeSans", "Liberation Sans", "SimHei",
        "MingLiU", "PMingLiU", "SimSun", "NSimSun", "FangSong"
    ]
    
    for fallback in fallback_fonts:
        try:
            font = pygame.font.SysFont(fallback, size, bold, italic)
            test_surface = font.render("áàảãạ", True, (255,255,255))
            if test_surface.get_width() > 0:
                return font
        except:
            continue
    
    return pygame.font.Font(None, size)

# Khởi tạo các font chính cho game
FONT_TITLE = get_font("Arial", 42, bold=True)
FONT_BTN = get_font("Arial", 18, bold=True)
FONT_HUD = get_font("Arial", 18, bold=True)
FONT_GUIDE = get_font("Arial", 16, bold=False)
FONT_STORY_TITLE = get_font("Arial", 36, bold=True)
FONT_STORY_TEXT = get_font("Arial", 18, bold=False)
FONT_STORY_SKIP = get_font("Arial", 14, bold=False)
FONT_GAMEOVER_TITLE = get_font("Arial", 52, bold=True)
FONT_GAMEOVER_BTN = get_font("Arial", 24, bold=True)
FONT_GAMEOVER_STATS = get_font("Arial", 20, bold=False)

# =========================================================================
# CẤU HÌNH KÍCH THƯỚC MAP SIÊU RỘNG
# =========================================================================
WORLD_WIDTH = 3600
WORLD_HEIGHT = 2800

# ĐỒNG BỘ MÀU SẮC
BG_WORLD = (24, 33, 24)        
BLOCK_GROUND = (38, 48, 38)     
STREET_COLOR = (45, 45, 48)    
LINE_YELLOW = (230, 180, 50)   

WHITE = (255, 255, 255)
YELLOW = (255, 255, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
GRAY = (70, 70, 70)
BLUE = (50, 150, 255)
PURPLE = (160, 32, 240)
DARK_GRAY = (35, 35, 38)

BLOCK_SIZE = 480
STREET_WIDTH = 144  

# ==========================================
# HÀM TIỆN ÍCH BẢN ĐỒ
# ==========================================
def is_on_street(x, y, w=0, h=0):
    """Kiểm tra xem một rect (x,y,w,h) có giao với đường không.
    Đường dọc: x_world % BLOCK_SIZE < STREET_WIDTH
    Đường ngang: y_world % BLOCK_SIZE < STREET_WIDTH
    """
    # Kiểm tra 4 góc + tâm của rect
    points = [
        (x, y), (x + w, y), (x, y + h), (x + w, y + h),
        (x + w // 2, y + h // 2)
    ]
    for px, py in points:
        if (px % BLOCK_SIZE) < STREET_WIDTH:
            return True
        if (py % BLOCK_SIZE) < STREET_WIDTH:
            return True
    return False

def is_in_land_block(x, y, w=0, h=0):
    """Ngược lại is_on_street – toàn bộ rect phải nằm trong ô đất."""
    # Đảm bảo tất cả 4 góc đều nằm trong cùng một ô đất
    corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
    for px, py in corners:
        if (px % BLOCK_SIZE) < STREET_WIDTH:
            return False
        if (py % BLOCK_SIZE) < STREET_WIDTH:
            return False
    return True

# Bảng giá tiền
PRICES = {
    "UMP": 250, "AK-47": 400, "Shotgun": 550,
    "Ammo_UMP": 30, "Ammo_AK": 50, "Ammo_Shotgun": 60,
    "Medkit": 40
}

# Cấu hình các màn chơi
LEVELS = {
    1: {"name": "Man 1: De", "zombie_speed_min": 0.6, "zombie_speed_max": 1.0, "spawn_rate": 60, "toxic_damage": 0.05, "duration_minutes": 0.5},
    2: {"name": "Man 2: Kho", "zombie_speed_min": 0.9, "zombie_speed_max": 1.3, "spawn_rate": 50, "toxic_damage": 0.15, "duration_minutes": 0.5},
    3: {"name": "Man 3: Sieu Kho + BOSS", "zombie_speed_min": 1.2, "zombie_speed_max": 1.5, "spawn_rate": 40, "toxic_damage": 0.3, "duration_minutes": 0.5}
}

shop_buttons = []
inv_buttons = []

# =========================================================================
# HỆ THỐNG CỐT TRUYỆN
# =========================================================================

STORY_PAGES = [
    {
        "title": "CHUONG 1: KHOI NGUON THAM HOA",
        "content": [
            "Ngay 15 thang 8 nam 2034, mot tham hoa bat ngo ap xuong thanh pho Metropolis.",
            "Mot vu no sinh hoc tai phong thi nghiem trung tam da giai phong 'Benh Xanh' -",
            "mot loai virus bien doi gen khien con nguoi tro len dien loan va mat kiem soat.",
            "",
            "Chi trong vong 48 gio, hang tram nghin nguoi da bien thanh nhung sinh vat",
            "hung han, chi con ban nang san moi va lay nhiem. Chinh phu sup do,",
            "cac thanh pho lon tro thanh dia nguc tran gian.",
            "",
            "Nhung dam may doc mau xanh lan toa khap noi, an mon da thit va",
            "huy diet moi su song. Giua hon loan, mot so it nguoi song sot mang trong",
            "minh khan the tu nhien - va ban la mot trong so ho.",
            "",
            "Tuy nhien, khan the chi giup ban chong lai su bien doi, chu khong bao ve",
            "ban khoi nhung moi nguy hiem chet nguoi cua vung dat hoang tan nay."
        ]
    },
    {
        "title": "CHUONG 2: NHIEM VU CUA BAN",
        "content": [
            "Ban tinh day trong mot can ham bo hoang o ngoai o phia Dong, noi ban da",
            "tru an suot 3 ngay qua. Tren tay la khu sung luc cu ky va mot it dan duoc,",
            "ben canh la chiec ba lo chua do tiep te it oi.",
            "",
            "Qua tan so radio song ngan, ban bat duoc tin nhan tu 'Tram Hy Vong' -",
            "can cu cuoi cung cua loai nguoi o phia Tay thanh pho. Ho dang co gang",
            "tong hop khan the tu mau cua nhung nguoi may man nhu ban de che tao",
            "thuoc giai doc.",
            "",
            "Nhiem vu cua ban: vuot qua 3 khu vuc nguy hiem nhat thanh pho,",
            "tim kiem tai nguyen, chien dau voi lu zombie dot bien, va cuoi cung la",
            "tieu diet ke dung dau - TYRANT BOSS ZOMBIE, sinh vat thi nghiem that bai",
            "mang suc manh huy diet nhat cua phong thi nghiem.",
            "",
            "Hay sinh ton! Hay chien dau! Tuong lai cua nhan loai dang o trong tay ban."
        ]
    },
    {
        "title": "CHUONG 3: LOI CANH BAO CUOI",
        "content": [
            "Truoc khi roi khoi no tru an, ban nhin lai buc tuong noi ban da viet",
            "nhung dong nhat ky ngan ngu: 'Ngay thu 1: con song, ngay thu 2: con hy vong',",
            "ngay thu 3: phai ra di'. Ban biet rang phia truoc la hang ngan xac song",
            "va nhung cam bay chet nguoi.",
            "",
            "Hay nho:",
            "• Tranh xa dam may doc mau xanh - chung se hut can sinh luc cua ban",
            "• Thu thap tien vang tu xac zombie de mua vu khi, dan duoc, va thuoc y te",
            "• Moi man choi chi keo dai 3 phut - hay song sot de tien xa hon",
            "• O man 3, TYRANT BOSS se xuat hien - hay tap trung hoa luc de ha guc no",
            "",
            "Ban that chat day deo ba lo, cam chac khu sung, va buoc ra khoi cua.",
            "",
            "Phia truoc la thanh pho nhiem doc...",
            "Chuc ban may man, nguoi song sot cuoi cung!"
        ]
    }
]

story_current_page = 0
story_displayed_lines = []
story_line_index = 0
story_last_update = 0
story_type_delay = 50
story_char_index = 0
story_current_line = ""
story_animation_active = False

def reset_story():
    global story_current_page, story_displayed_lines, story_line_index
    global story_last_update, story_char_index, story_current_line, story_animation_active
    
    story_current_page = 0
    story_displayed_lines = []
    story_line_index = 0
    story_last_update = 0
    story_char_index = 0
    story_current_line = ""
    story_animation_active = True

def update_story_animation():
    global story_current_page, story_displayed_lines, story_line_index
    global story_last_update, story_char_index, story_current_line, story_animation_active
    
    if not story_animation_active:
        return
        
    current_time = pygame.time.get_ticks()
    
    if story_line_index >= len(STORY_PAGES[story_current_page]["content"]):
        story_animation_active = False
        return
    
    if story_char_index == 0:
        story_current_line = STORY_PAGES[story_current_page]["content"][story_line_index]
    
    if current_time - story_last_update >= story_type_delay:
        story_last_update = current_time
        if story_char_index < len(story_current_line):
            story_char_index += 1
        else:
            if story_current_line:
                story_displayed_lines.append(story_current_line)
            story_line_index += 1
            story_char_index = 0
            story_current_line = ""

def draw_story_screen(surface):
    surface.fill((5, 8, 5))
    
    for _ in range(50):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        pygame.draw.circle(surface, (15, 20, 12), (x, y), random.randint(1, 3))
    
    border_rect = pygame.Rect(40, 40, SCREEN_WIDTH - 80, SCREEN_HEIGHT - 80)
    pygame.draw.rect(surface, (20, 30, 20), border_rect, border_radius=10)
    pygame.draw.rect(surface, (60, 150, 70), border_rect, 2, border_radius=10)
    
    title = STORY_PAGES[story_current_page]["title"]
    title_surf = FONT_STORY_TITLE.render(title, True, (180, 255, 100))
    surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 70))
    
    pygame.draw.line(surface, (60, 150, 70), (70, 110), (SCREEN_WIDTH - 70, 110), 1)
    
    y_offset = 140
    line_height = 26
    
    for i, line in enumerate(story_displayed_lines):
        if line:
            line_surf = FONT_STORY_TEXT.render(line, True, (200, 220, 190))
            surface.blit(line_surf, (70, y_offset + i * line_height))
    
    if story_animation_active and story_char_index < len(story_current_line) and story_current_line:
        partial_line = story_current_line[:story_char_index]
        if partial_line:
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                partial_line += "█"
            line_surf = FONT_STORY_TEXT.render(partial_line, True, (220, 255, 200))
            surface.blit(line_surf, (70, y_offset + len(story_displayed_lines) * line_height))
    
    skip_text = "Nhan [ENTER] hoac [SPACE] de bo qua / sang trang tiep theo"
    skip_surf = FONT_STORY_SKIP.render(skip_text, True, (100, 150, 100))
    surface.blit(skip_surf, (SCREEN_WIDTH // 2 - skip_surf.get_width() // 2, SCREEN_HEIGHT - 40))
    
    page_text = f"Trang {story_current_page + 1}/{len(STORY_PAGES)}"
    page_surf = FONT_STORY_SKIP.render(page_text, True, (120, 180, 120))
    surface.blit(page_surf, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 40))

def handle_story_input():
    global story_current_page, story_animation_active
    global story_displayed_lines, story_line_index, story_char_index, story_current_line
    
    if story_animation_active:
        if story_char_index < len(story_current_line):
            story_char_index = len(story_current_line)
            story_last_update = pygame.time.get_ticks()
            return "STAY"
    
    if story_line_index >= len(STORY_PAGES[story_current_page]["content"]):
        if story_current_page < len(STORY_PAGES) - 1:
            story_current_page += 1
            story_displayed_lines = []
            story_line_index = 0
            story_char_index = 0
            story_current_line = ""
            story_animation_active = True
            return "STAY"
        else:
            return "EXIT_STORY"
    
    return "STAY"

# =========================================================================
# MÀN HÌNH GAME OVER
# =========================================================================

def draw_gameover_screen(surface, score, gold, level_name):
    """Vẽ màn hình Game Over với các tùy chọn"""
    # Nền tối với hiệu ứng máu
    surface.fill((8, 5, 5))
    
    # Vẽ hiệu ứng vết máu
    for _ in range(100):
        x = random.randint(0, SCREEN_WIDTH)
        y = random.randint(0, SCREEN_HEIGHT)
        blood_color = (random.randint(100, 180), random.randint(20, 50), random.randint(20, 50))
        pygame.draw.circle(surface, blood_color, (x, y), random.randint(1, 4))
    
    # Khung viền đỏ
    border_rect = pygame.Rect(50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100)
    pygame.draw.rect(surface, (30, 10, 10), border_rect, border_radius=15)
    pygame.draw.rect(surface, RED, border_rect, 3, border_radius=15)
    
    # Tiêu đề GAME OVER
    title_surf = FONT_GAMEOVER_TITLE.render("GAME OVER", True, RED)
    title_shadow = FONT_GAMEOVER_TITLE.render("GAME OVER", True, (80, 0, 0))
    surface.blit(title_shadow, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + 3, 83))
    surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 80))
    
    # Đường kẻ
    pygame.draw.line(surface, RED, (100, 140), (SCREEN_WIDTH - 100, 140), 2)
    
    # Thống kê
    stats_y = 170
    stat_color = (220, 200, 200)
    
    # Icon skull
    skull_font = get_font("Segoe UI Symbol", 24, bold=True)
    skull_surf = skull_font.render("💀", True, RED)
    surface.blit(skull_surf, (SCREEN_WIDTH // 2 - 180, stats_y - 5))
    
    kills_text = FONT_GAMEOVER_STATS.render(f"Zombie da diet: {score}", True, stat_color)
    surface.blit(kills_text, (SCREEN_WIDTH // 2 - kills_text.get_width() // 2, stats_y))
    
    # Icon coin
    coin_font = get_font("Segoe UI Symbol", 24, bold=True)
    coin_surf = coin_font.render("💰", True, YELLOW)
    surface.blit(coin_surf, (SCREEN_WIDTH // 2 - 180, stats_y + 45))
    
    gold_text = FONT_GAMEOVER_STATS.render(f"Tong tien thu duoc: ${gold}", True, YELLOW)
    surface.blit(gold_text, (SCREEN_WIDTH // 2 - gold_text.get_width() // 2, stats_y + 45))
    
    # Icon level
    level_font = get_font("Segoe UI Symbol", 24, bold=True)
    level_surf = level_font.render("⚠️", True, (255, 100, 100))
    surface.blit(level_surf, (SCREEN_WIDTH // 2 - 180, stats_y + 90))
    
    level_text = FONT_GAMEOVER_STATS.render(f"Man choi: {level_name}", True, (255, 150, 150))
    surface.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, stats_y + 90))
    
    # Vẽ nút bấm
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}
    
    # Nút CHƠI LẠI
    retry_rect = pygame.Rect(SCREEN_WIDTH // 2 - 220, 350, 200, 55)
    if retry_rect.collidepoint(mouse_pos):
        pygame.draw.rect(surface, (40, 120, 40), retry_rect, border_radius=10)
        pygame.draw.rect(surface, GREEN, retry_rect, 2, border_radius=10)
        btn_color = (220, 255, 220)
    else:
        pygame.draw.rect(surface, (20, 70, 20), retry_rect, border_radius=10)
        pygame.draw.rect(surface, (50, 150, 50), retry_rect, 2, border_radius=10)
        btn_color = (150, 200, 150)
    
    retry_icon = get_font("Segoe UI Symbol", 28, bold=True).render("↺", True, btn_color)
    surface.blit(retry_icon, (retry_rect.x + 20, retry_rect.y + 12))
    
    retry_text = FONT_GAMEOVER_BTN.render("CHOI LAI", True, btn_color)
    surface.blit(retry_text, (retry_rect.x + 55, retry_rect.y + 13))
    buttons["retry"] = retry_rect
    
    # Nút THOÁT
    quit_rect = pygame.Rect(SCREEN_WIDTH // 2 + 20, 350, 200, 55)
    if quit_rect.collidepoint(mouse_pos):
        pygame.draw.rect(surface, (120, 30, 30), quit_rect, border_radius=10)
        pygame.draw.rect(surface, RED, quit_rect, 2, border_radius=10)
        btn_color = (255, 200, 200)
    else:
        pygame.draw.rect(surface, (70, 20, 20), quit_rect, border_radius=10)
        pygame.draw.rect(surface, (150, 50, 50), quit_rect, 2, border_radius=10)
        btn_color = (200, 150, 150)
    
    quit_icon = get_font("Segoe UI Symbol", 28, bold=True).render("✕", True, btn_color)
    surface.blit(quit_icon, (quit_rect.x + 20, quit_rect.y + 12))
    
    quit_text = FONT_GAMEOVER_BTN.render("THOAT", True, btn_color)
    surface.blit(quit_text, (quit_rect.x + 55, quit_rect.y + 13))
    buttons["quit"] = quit_rect
    
    # Hướng dẫn
    tip_font = get_font("Arial", 12, bold=False)
    tip_text = tip_font.render("Nhan phim [R] de Choi Lai | [ESC] de Thoat", True, (100, 80, 80))
    surface.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, SCREEN_HEIGHT - 50))
    
    return buttons

# =========================================================================
# TẢI HÌNH ẢNH ICON
# =========================================================================
def load_shop_icon(filename, default_color, size=(40, 25)):
    if os.path.exists(filename):
        try:
            img = pygame.image.load(filename).convert_alpha()
            return pygame.transform.scale(img, size)
        except pygame.error:
            pass
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(default_color)
    pygame.draw.rect(surf, WHITE, (0, 0, size[0], size[1]), 1)
    return surf

icon_pistol  = load_shop_icon("pistol.png", (120, 120, 120))
icon_ump     = load_shop_icon("ump.png", (50, 150, 50))
icon_ak47    = load_shop_icon("ak47.png", (150, 50, 50))
icon_shotgun = load_shop_icon("shotgun.png", (50, 50, 150))
icon_ammo    = load_shop_icon("ammo.png", (200, 180, 50), size=(24, 24))
icon_medkit  = load_shop_icon("medkit.png", (220, 50, 50), size=(24, 24))
icon_shop_hud = load_shop_icon("shop_hud.png", BLUE, size=(24, 24))
icon_bag_hud  = load_shop_icon("bag_hud.png", PURPLE, size=(24, 24))

# =========================================================================
# HÀM CẮT SPRITESHEET
# =========================================================================
def load_spritesheet(filename, cols=4, rows=4, target_size=(65, 65)):
    try:
        sheet = pygame.image.load(filename).convert_alpha()
    except pygame.error:
        sheet = pygame.surface.Surface((256, 256))
        sheet.fill((200, 200, 200))
        
    sheet_width, sheet_height = sheet.get_size()
    cell_width = sheet_width // cols
    cell_height = sheet_height // rows
    
    animations = {"down": [], "left": [], "right": [], "up": []}
    keys = ["down", "left", "right", "up"] 
    
    for row in range(rows):
        direction = keys[row]
        for col in range(cols):
            rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
            image = pygame.Surface(rect.size, pygame.SRCALPHA)
            image.blit(sheet, (0, 0), rect)
            image = pygame.transform.scale(image, target_size)
            animations[direction].append(image)
            
    return animations

# ==========================================
# LỚP TÒA NHÀ
# ==========================================
class Building(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, raw_image):
        super().__init__()
        if raw_image:
            self.image = pygame.transform.scale(raw_image, (width, height))
        else:
            self.image = pygame.surface.Surface((width, height))
            self.image.fill(GRAY)
            pygame.draw.rect(self.image, WHITE, (0, 0, width, height), 1)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

# ==========================================
# LỚP CỘT ĐÈN ĐƯỜNG
# ==========================================
class Streetlight(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            raw_image = pygame.image.load("streetlight.png").convert_alpha()
            self.image = pygame.transform.scale(raw_image, (24, 45))
        except pygame.error:
            self.image = pygame.Surface((24, 45))
            self.image.fill((100, 100, 105))
            pygame.draw.rect(self.image, YELLOW, (8, 0, 8, 8))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# ==========================================
# LỚP NẮP CỐNG
# ==========================================
class Manhole(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (30, 30, 32), (12, 12), 11)
        pygame.draw.circle(self.image, (55, 55, 58), (12, 12), 9)
        pygame.draw.line(self.image, (35, 35, 38), (12, 5), (12, 19), 2)
        pygame.draw.line(self.image, (35, 35, 38), (5, 12), (19, 12), 2)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

# ==========================================
# LỚP ĐÁM MÂY ĐỘC
# ==========================================
class ToxicZone(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.total_size = 280
        self.image = pygame.Surface((self.total_size, self.total_size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.center_x = float(x)
        self.center_y = float(y)
        self.vel_x = random.uniform(-0.4, 0.4)
        self.vel_y = random.uniform(-0.4, 0.4)
        
        self.toxic_img = None
        for ext in ["toxic.png", "toxic.jpg", "toxic.jpeg"]:
            if os.path.exists(ext):
                try:
                    raw_img = pygame.image.load(ext).convert_alpha()
                    self.toxic_img = pygame.transform.scale(raw_img, (self.total_size, self.total_size))
                    break
                except pygame.error:
                    pass

        self.puffs = []
        if not self.toxic_img:
            num_puffs = random.randint(5, 7)
            for _ in range(num_puffs):
                off_x = random.randint(-50, 50)
                off_y = random.randint(-50, 50)
                base_r = random.randint(35, 55)
                speed = random.uniform(0.02, 0.05)
                angle = random.uniform(0, 6.28)
                self.puffs.append({"ox": off_x, "oy": off_y, "r": base_r, "speed": speed, "angle": angle})

    def update(self):
        self.center_x += self.vel_x
        self.center_y += self.vel_y
        self.rect.centerx = int(self.center_x)
        self.rect.centery = int(self.center_y)
        
        if self.rect.left < 50 or self.rect.right > WORLD_WIDTH - 50: self.vel_x *= -1
        if self.rect.top < 50 or self.rect.bottom > WORLD_HEIGHT - 50: self.vel_y *= -1

        self.image.fill((0, 0, 0, 0))
        
        if self.toxic_img:
            self.image.blit(self.toxic_img, (0, 0))
        else:
            canvas_center = self.total_size // 2
            for puff in self.puffs:
                puff["angle"] += puff["speed"]
                current_r = puff["r"] + int(math.sin(puff["angle"]) * 6)
                cx = canvas_center + puff["ox"]
                cy = canvas_center + puff["oy"]
                pygame.draw.circle(self.image, (0, 200, 60, 25), (cx, cy), current_r)
                pygame.draw.circle(self.image, (0, 225, 70, 45), (cx, cy), int(current_r * 0.8))
                pygame.draw.circle(self.image, (20, 255, 90, 75), (cx, cy), int(current_r * 0.5))

    def check_player_collision(self, player_rect):
        dist = math.hypot(player_rect.centerx - self.rect.centerx, player_rect.centery - self.rect.centery)
        return dist < (self.total_size // 2 - 20)

# ==========================================
# LỚP ĐỒNG XU
# ==========================================
class Coin(pygame.sprite.Sprite):
    MAGNET_RADIUS = 80    # khoảng cách bắt đầu hút
    MAGNET_SPEED  = 6.0   # tốc độ hút về phía player

    def __init__(self, x, y, value):
        super().__init__()
        self.value = value
        self.pos_x = float(x)
        self.pos_y = float(y)
        self._draw_image(12)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self._magnet_active = False

    def _draw_image(self, radius):
        size = radius * 2
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (radius, radius), radius)
        pygame.draw.circle(self.image, WHITE,  (radius, radius), radius, 1)

    def update(self, player_rect=None, *args):
        """Nếu player_rect được cung cấp, kiểm tra hút."""
        if player_rect is None:
            return
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        dist = math.hypot(dx, dy)
        if dist < self.MAGNET_RADIUS and dist > 0:
            self._magnet_active = True
            # Tăng tốc khi càng gần
            speed = self.MAGNET_SPEED * (1.0 + (self.MAGNET_RADIUS - dist) / self.MAGNET_RADIUS * 3)
            self.pos_x += (dx / dist) * speed
            self.pos_y += (dy / dist) * speed
            self.rect.center = (int(self.pos_x), int(self.pos_y))
        else:
            self._magnet_active = False

# ==========================================
# LỚP VIÊN ĐẠN
# ==========================================
class Bullet(pygame.sprite.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, damage):
        super().__init__()
        self.image = pygame.Surface((6, 6), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (3, 3), 3)
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)
        self.pos_x = float(start_x)
        self.pos_y = float(start_y)
        
        dx = target_x - start_x
        dy = target_y - start_y
        distance = math.hypot(dx, dy)
        if distance == 0: distance = 1
            
        self.speed = 16
        self.velocity_x = (dx / distance) * self.speed
        self.velocity_y = (dy / distance) * self.speed
        self.damage = damage  

    def update(self):
        self.pos_x += self.velocity_x
        self.pos_y += self.velocity_y
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        if (self.rect.bottom < 0 or self.rect.top > WORLD_HEIGHT or 
            self.rect.right < 0 or self.rect.left > WORLD_WIDTH):
            self.kill()

# ==========================================
# LỚP NHÂN VẬT PLAYER
# ==========================================
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        # Tải sprite sheets cho từng loại súng
        self.all_weapon_animations = {
            "Pistol":  load_spritesheet("player_pistol.png") if os.path.exists("player_pistol.png") else load_spritesheet("player_spritesheet.png"),
            "UMP":     load_spritesheet("player_ump.png") if os.path.exists("player_ump.png") else load_spritesheet("player_spritesheet.png"),
            "AK-47":   load_spritesheet("player_ak47.png") if os.path.exists("player_ak47.png") else load_spritesheet("player_spritesheet.png"),
            "Shotgun": load_spritesheet("player_shotgun.png") if os.path.exists("player_shotgun.png") else load_spritesheet("player_spritesheet.png")
        }
        
        self.current_weapon = "Pistol"
        self.animations = self.all_weapon_animations[self.current_weapon]
        
        self.current_direction = "down"
        self.frame_index = 0
        self.image = self.animations[self.current_direction][self.frame_index]
        
        self.rect = self.image.get_rect()
        self.rect.center = (WORLD_WIDTH // 2 + 100, WORLD_HEIGHT // 2 + 100)
        self.speed = 5

        # === DASH / SPRINT (phím SPACE) ===
        self.dash_speed = 12          # tốc độ khi lướt
        self.dash_duration = 200      # ms lướt mỗi lần
        self.dash_cooldown = 800      # ms hồi chiêu
        self.is_dashing = False
        self.dash_start_time = 0
        self.last_dash_time = 0
        self.dash_dir_x = 0
        self.dash_dir_y = 0
        
        # Tọa độ float cho di chuyển mượt
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        
        self.max_hp = 500
        self.hp = 500
        self.gold = 1000  
        self.last_shot_time = 0

        self.is_reloading = False
        self.reload_start_time = 0
        self.reload_duration = 1500  

        self.weapons = {
            "Pistol":  {"damage": 10,  "cooldown": 300, "mag_size": 7,  "current_mag": 7},
            "UMP":     {"damage": 15, "cooldown": 140, "mag_size": 30, "current_mag": 30},
            "AK-47":   {"damage": 30, "cooldown": 200, "mag_size": 30, "current_mag": 30},
            "Shotgun": {"damage": 25, "cooldown": 600, "mag_size": 6,  "current_mag": 6}
        }

        self.inventory = {
            "Pistol": True, "UMP": False, "AK-47": False, "Shotgun": False,
            "Ammo_UMP": 0, "Ammo_AK": 0, "Ammo_Shotgun": 0, "Medkit": 0
        }

    def update(self, obstacles):
        current_time = pygame.time.get_ticks()

        if self.is_reloading:
            if current_time - self.reload_start_time >= self.reload_duration:
                self.complete_reload_logic()

        keys = pygame.key.get_pressed()
        moving = False
        move_x, move_y = 0, 0
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_x = -self.speed
            moving = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_x = self.speed
            moving = True
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            move_y = -self.speed
            moving = True
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            move_y = self.speed
            moving = True
        
        # Chuẩn hóa vector khi di chuyển chéo
        if move_x != 0 and move_y != 0:
            move_x *= 0.7071
            move_y *= 0.7071

        # === XỬ LÝ DASH (SPACE) ===
        # Kích hoạt dash khi nhấn SPACE và đang di chuyển, hết cooldown
        if keys[pygame.K_SPACE] and not self.is_dashing:
            if current_time - self.last_dash_time >= self.dash_cooldown:
                # Lướt theo hướng đang đi, nếu đứng yên lướt về hướng nhìn chuột
                if move_x != 0 or move_y != 0:
                    raw_dx = move_x
                    raw_dy = move_y
                else:
                    # Dùng hướng chuột làm hướng dash
                    mx, my = pygame.mouse.get_pos()
                    raw_dx = mx - SCREEN_WIDTH // 2
                    raw_dy = my - SCREEN_HEIGHT // 2
                mag = math.hypot(raw_dx, raw_dy)
                if mag > 0:
                    self.dash_dir_x = raw_dx / mag
                    self.dash_dir_y = raw_dy / mag
                    self.is_dashing = True
                    self.dash_start_time = current_time
                    self.last_dash_time = current_time

        if self.is_dashing:
            if current_time - self.dash_start_time < self.dash_duration:
                move_x = self.dash_dir_x * self.dash_speed
                move_y = self.dash_dir_y * self.dash_speed
                moving = True
            else:
                self.is_dashing = False
        
        new_x = self.pos_x + move_x
        new_y = self.pos_y + move_y
        
        # Xử lý va chạm X
        self.rect.centerx = new_x
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        for block in collision_list:
            if move_x > 0:
                self.rect.right = block.rect.left
            elif move_x < 0:
                self.rect.left = block.rect.right
        self.pos_x = self.rect.centerx
        
        # Xử lý va chạm Y
        self.rect.centery = new_y
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        for block in collision_list:
            if move_y > 0:
                self.rect.bottom = block.rect.top
            elif move_y < 0:
                self.rect.top = block.rect.bottom
        self.pos_y = self.rect.centery
        
        # Giới hạn world
        if self.rect.left < 0:
            self.rect.left = 0
            self.pos_x = self.rect.centerx
        if self.rect.right > WORLD_WIDTH:
            self.rect.right = WORLD_WIDTH
            self.pos_x = self.rect.centerx
        if self.rect.top < 0:
            self.rect.top = 0
            self.pos_y = self.rect.centery
        if self.rect.bottom > WORLD_HEIGHT:
            self.rect.bottom = WORLD_HEIGHT
            self.pos_y = self.rect.centery

        # Xác định hướng theo chuột
        screen_center_x = SCREEN_WIDTH // 2
        screen_center_y = SCREEN_HEIGHT // 2
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        rel_x = mouse_x - screen_center_x
        rel_y = mouse_y - screen_center_y
        
        if abs(rel_x) > abs(rel_y):
            self.current_direction = "right" if rel_x > 0 else "left"
        else:
            self.current_direction = "down" if rel_y > 0 else "up"

        # Animation
        if moving:
            self.frame_index += 0.15
            if self.frame_index >= len(self.animations[self.current_direction]):
                self.frame_index = 0
            self.image = self.animations[self.current_direction][int(self.frame_index)]
        else:
            self.image = self.animations[self.current_direction][0]

    def start_reload_sequence(self):
        w = self.weapons[self.current_weapon]
        if w["current_mag"] == w["mag_size"]:
            return

        has_ammo = False
        if self.current_weapon == "Pistol": 
            has_ammo = True
        elif self.current_weapon == "UMP" and self.inventory["Ammo_UMP"] > 0: 
            has_ammo = True
        elif self.current_weapon == "AK-47" and self.inventory["Ammo_AK"] > 0: 
            has_ammo = True
        elif self.current_weapon == "Shotgun" and self.inventory["Ammo_Shotgun"] > 0: 
            has_ammo = True

        if not has_ammo:
            return
            
        if not self.is_reloading:
            self.is_reloading = True
            self.reload_start_time = pygame.time.get_ticks()

    def complete_reload_logic(self):
        w = self.weapons[self.current_weapon]
        needed = w["mag_size"] - w["current_mag"]
        
        if self.current_weapon == "Pistol":
            w["current_mag"] = w["mag_size"]
        elif self.current_weapon == "UMP":
            transfer = min(needed, self.inventory["Ammo_UMP"])
            w["current_mag"] += transfer
            self.inventory["Ammo_UMP"] -= transfer
        elif self.current_weapon == "AK-47":
            transfer = min(needed, self.inventory["Ammo_AK"])
            w["current_mag"] += transfer
            self.inventory["Ammo_AK"] -= transfer
        elif self.current_weapon == "Shotgun":
            transfer = min(needed, self.inventory["Ammo_Shotgun"])
            w["current_mag"] += transfer
            self.inventory["Ammo_Shotgun"] -= transfer
            
        self.is_reloading = False

    def switch_weapon_quick(self):
        available_weapons = []
        if self.inventory["Pistol"]: available_weapons.append("Pistol")
        if self.inventory["UMP"]: available_weapons.append("UMP")
        if self.inventory["AK-47"]: available_weapons.append("AK-47")
        if self.inventory["Shotgun"]: available_weapons.append("Shotgun")
        
        if not available_weapons:
            return
            
        try:
            current_idx = available_weapons.index(self.current_weapon)
            next_idx = (current_idx + 1) % len(available_weapons)
        except ValueError:
            next_idx = 0
            
        self.current_weapon = available_weapons[next_idx]
        self.animations = self.all_weapon_animations[self.current_weapon]
        self.frame_index = 0
        self.is_reloading = False

    def shoot(self, camera):
        if self.is_reloading:
            return None

        w = self.weapons[self.current_weapon]
        current_time = pygame.time.get_ticks()
        
        if w["current_mag"] <= 0:
            self.start_reload_sequence()
            return None
        
        if current_time - self.last_shot_time >= w["cooldown"]:
            self.last_shot_time = current_time
            w["current_mag"] -= 1            
            mouse_x, mouse_y = pygame.mouse.get_pos()
            target_x = mouse_x + camera.x
            target_y = mouse_y + camera.y
            
            bullets_created = []
            
            if self.current_weapon == "Shotgun":
                base_angle = math.atan2(target_y - self.rect.centery, target_x - self.rect.centerx)
                spread_angles = [-0.2, -0.1, 0, 0.1, 0.2]
                for angle_offset in spread_angles:
                    final_angle = base_angle + angle_offset
                    tx = self.rect.centerx + math.cos(final_angle) * 100
                    ty = self.rect.centery + math.sin(final_angle) * 100
                    bullets_created.append(Bullet(self.rect.centerx, self.rect.centery, tx, ty, w["damage"]))
            else:
                bullets_created.append(Bullet(self.rect.centerx, self.rect.centery, target_x, target_y, w["damage"]))
            
            if w["current_mag"] <= 0:
                self.start_reload_sequence()

            return bullets_created
        return None

    def draw_hud(self, surface, font, score, current_level_name, remaining_seconds):
        bar_x, bar_y, bar_width, bar_height = 15, 35, 200, 15
        hp_pct = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * hp_pct)
        color = GREEN if hp_pct > 0.4 else RED
        
        pygame.draw.rect(surface, GRAY, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill_width, bar_height))
        pygame.draw.rect(surface, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)

        hp_text = font.render(f"HP {int(self.hp)}/{self.max_hp}", True, WHITE)
        surface.blit(hp_text, (15, 12))
        
        gold_text = font.render(f"$ {self.gold}", True, YELLOW)
        surface.blit(gold_text, (15, 58))
        score_text = font.render(f"Kills: {score} | {current_level_name}", True, WHITE)
        surface.blit(score_text, (15, 80))

        mins = int(remaining_seconds) // 60
        secs = int(remaining_seconds) % 60
        time_text = font.render(f"Thoi gian qua man: {mins:02d}:{secs:02d}", True, YELLOW)
        surface.blit(time_text, (15, 105))

        paused_hint = font.render("Bam [ ESC ] de Tam Dung", True, WHITE)
        surface.blit(paused_hint, (15, 130))

        # === HIỆN TRẠNG THÁI DASH (SPACE) ===
        current_time_hud = pygame.time.get_ticks()
        cooldown_left = max(0, self.dash_cooldown - (current_time_hud - self.last_dash_time))
        if self.is_dashing:
            dash_label = "LUOT: DANG LUOT!"
            dash_color = (100, 220, 255)
        elif cooldown_left > 0:
            dash_label = f"LUOT: {cooldown_left // 100 / 10:.1f}s"
            dash_color = (180, 180, 180)
        else:
            dash_label = "LUOT: [SPACE] San sang!"
            dash_color = (100, 255, 180)
        dash_surf = font.render(dash_label, True, dash_color)
        surface.blit(dash_surf, (15, 152))
        
        w = self.weapons[self.current_weapon]
        if self.current_weapon == "Pistol": 
            ammo_bag = "INF"
        elif self.current_weapon == "UMP": 
            ammo_bag = self.inventory["Ammo_UMP"]
        elif self.current_weapon == "AK-47": 
            ammo_bag = self.inventory["Ammo_AK"]
        elif self.current_weapon == "Shotgun": 
            ammo_bag = self.inventory["Ammo_Shotgun"]
        
        if self.is_reloading:
            weapon_text = font.render(f"{self.current_weapon} [DANG THAY DAN...]", True, RED)
        else:
            weapon_text = font.render(f"{self.current_weapon} [{w['current_mag']}/{ammo_bag}]", True, BLUE)
        surface.blit(weapon_text, (15, SCREEN_HEIGHT - 35))

        controls = [
            {"key": "P", "icon": icon_shop_hud, "bg": BLUE},
            {"key": "I", "icon": icon_bag_hud,  "bg": PURPLE},
            {"key": "R", "icon": None,          "bg": GRAY,   "label": "RELOAD"},
            {"key": "Q", "icon": None,          "bg": GRAY,   "label": "SWAP"}
        ]
        
        start_button_x = SCREEN_WIDTH - 240
        button_y = SCREEN_HEIGHT - 45
        
        for ctrl in controls:
            pygame.draw.rect(surface, DARK_GRAY, (start_button_x, button_y, 50, 32), border_radius=6)
            pygame.draw.rect(surface, ctrl["bg"], (start_button_x, button_y, 50, 32), 1, border_radius=6)
            key_lbl = font.render(ctrl["key"], True, YELLOW)
            surface.blit(key_lbl, (start_button_x + 5, button_y + 2))
            if ctrl["icon"]:
                surface.blit(ctrl["icon"], (start_button_x + 22, button_y + 4))
            elif "label" in ctrl:
                mini_lbl = pygame.font.SysFont("Arial", 10, bold=True).render(ctrl["label"], True, WHITE)
                surface.blit(mini_lbl, (start_button_x + 14, button_y + 16))
            start_button_x += 58

    def draw_reload_text(self, surface, camera, font):
        w = self.weapons[self.current_weapon]
        
        if self.is_reloading:
            ammo_str = f"DANG THAY DAN... ({w['current_mag']})"
            text_color = RED
        else:
            if self.current_weapon == "Pistol":
                ammo_str = f"{w['current_mag']} / INF"
            elif self.current_weapon == "UMP":
                ammo_str = f"{w['current_mag']} / {self.inventory['Ammo_UMP']}"
            elif self.current_weapon == "AK-47":
                ammo_str = f"{w['current_mag']} / {self.inventory['Ammo_AK']}"
            elif self.current_weapon == "Shotgun":
                ammo_str = f"{w['current_mag']} / {self.inventory['Ammo_Shotgun']}"
            text_color = YELLOW if w['current_mag'] <= (w['mag_size'] * 0.25) else WHITE

        ammo_text = font.render(ammo_str, True, text_color)
        tx = (self.rect.centerx - camera.x) - (ammo_text.get_width() // 2)
        ty = (self.rect.top - camera.y) - 20
        surface.blit(ammo_text, (tx, ty))

# ==========================================
# HỆ THỐNG TÌM ĐƯỜNG (PATHFINDING)
# ==========================================
# Grid nhỏ dùng cho zombie pathfinding (mỗi ô = 60px)
_PF_CELL = 60
_PF_COLS = WORLD_WIDTH  // _PF_CELL + 1
_PF_ROWS = WORLD_HEIGHT // _PF_CELL + 1
_pf_blocked = None   # set of (col, row) – cập nhật khi init map

def pf_build_grid(obstacles):
    """Xây dựng tập ô bị chặn từ danh sách obstacles (buildings)."""
    global _pf_blocked
    blocked = set()
    for obs in obstacles:
        r = obs.rect
        c0 = max(0, (r.left   - 4) // _PF_CELL)
        c1 = min(_PF_COLS - 1, (r.right  + 4) // _PF_CELL)
        r0 = max(0, (r.top    - 4) // _PF_CELL)
        r1 = min(_PF_ROWS - 1, (r.bottom + 4) // _PF_CELL)
        for cc in range(c0, c1 + 1):
            for rr in range(r0, r1 + 1):
                blocked.add((cc, rr))
    _pf_blocked = blocked

def _pf_neighbors(col, row):
    for dc, dr in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
        nc, nr = col + dc, row + dr
        if 0 <= nc < _PF_COLS and 0 <= nr < _PF_ROWS and (nc, nr) not in _pf_blocked:
            yield nc, nr

def _cell(wx, wy):
    return int(wx) // _PF_CELL, int(wy) // _PF_CELL

def _cell_world(col, row):
    return col * _PF_CELL + _PF_CELL // 2, row * _PF_CELL + _PF_CELL // 2

def bfs_next_step(sx, sy, tx, ty):
    """BFS từ (sx,sy) đến (tx,ty) → trả về (nx,ny) bước kế tiếp trong world coords."""
    if _pf_blocked is None:
        return tx, ty
    sc = _cell(sx, sy)
    tc = _cell(tx, ty)
    if sc == tc:
        return tx, ty
    from collections import deque
    queue = deque()
    queue.append((sc, None))
    came_from = {sc: None}
    found = False
    steps = 0
    while queue and steps < 600:
        cur, _ = queue.popleft()
        steps += 1
        if cur == tc:
            found = True
            break
        for nb in _pf_neighbors(*cur):
            if nb not in came_from:
                came_from[nb] = cur
                queue.append((nb, None))
    if not found:
        return tx, ty
    # Truy vết path → lấy bước đầu tiên
    path = []
    node = tc
    while node and node != sc:
        path.append(node)
        node = came_from.get(node)
    if not path:
        return tx, ty
    next_cell = path[-1]
    wx, wy = _cell_world(*next_cell)
    return float(wx), float(wy)

def dfs_next_step(sx, sy, tx, ty, zombie_id):
    """DFS lấy bước kế tiếp (có giới hạn depth để tránh đường xấu)."""
    if _pf_blocked is None:
        return tx, ty
    sc = _cell(sx, sy)
    tc = _cell(tx, ty)
    if sc == tc:
        return tx, ty
    # DFS với depth limit
    stack = [(sc, [sc])]
    visited = {sc}
    best_path = None
    max_depth = 30
    while stack:
        cur, path = stack.pop()
        if cur == tc:
            best_path = path
            break
        if len(path) >= max_depth:
            continue
        # Sắp xếp theo heuristic để DFS "có hướng" hơn một chút
        neighbors = list(_pf_neighbors(*cur))
        neighbors.sort(key=lambda nb: math.hypot(nb[0]-tc[0], nb[1]-tc[1]))
        for nb in reversed(neighbors):  # reversed vì stack LIFO
            if nb not in visited:
                visited.add(nb)
                stack.append((nb, path + [nb]))
    if best_path is None or len(best_path) < 2:
        return tx, ty
    next_cell = best_path[1]
    wx, wy = _cell_world(*next_cell)
    return float(wx), float(wy)

def astar_next_step(sx, sy, tx, ty):
    """A* tìm đường ngắn nhất từ (sx,sy) đến (tx,ty)."""
    if _pf_blocked is None:
        return tx, ty
    sc = _cell(sx, sy)
    tc = _cell(tx, ty)
    if sc == tc:
        return tx, ty
    import heapq
    open_set = []
    heapq.heappush(open_set, (0, sc))
    came_from = {sc: None}
    g_score = {sc: 0}
    steps = 0
    while open_set and steps < 800:
        _, cur = heapq.heappop(open_set)
        steps += 1
        if cur == tc:
            break
        for nb in _pf_neighbors(*cur):
            dc = 1 if (nb[0] == cur[0] or nb[1] == cur[1]) else 1.414
            tentative_g = g_score[cur] + dc
            if nb not in g_score or tentative_g < g_score[nb]:
                g_score[nb] = tentative_g
                h = math.hypot(nb[0] - tc[0], nb[1] - tc[1])
                f = tentative_g + h
                heapq.heappush(open_set, (f, nb))
                came_from[nb] = cur
    if tc not in came_from:
        return tx, ty
    path = []
    node = tc
    while node and node != sc:
        path.append(node)
        node = came_from.get(node)
    if not path:
        return tx, ty
    next_cell = path[-1]
    wx, wy = _cell_world(*next_cell)
    return float(wx), float(wy)

def heuristic_next_step(sx, sy, tx, ty):
    """Heuristic: greedy best-first – chọn hàng xóm gần đích nhất."""
    if _pf_blocked is None:
        return tx, ty
    sc = _cell(sx, sy)
    tc = _cell(tx, ty)
    if sc == tc:
        return tx, ty
    import heapq
    open_set = []
    heapq.heappush(open_set, (0, sc))
    came_from = {sc: None}
    visited = {sc}
    steps = 0
    while open_set and steps < 500:
        _, cur = heapq.heappop(open_set)
        steps += 1
        if cur == tc:
            break
        for nb in _pf_neighbors(*cur):
            if nb not in visited:
                visited.add(nb)
                h = math.hypot(nb[0] - tc[0], nb[1] - tc[1])
                heapq.heappush(open_set, (h, nb))
                came_from[nb] = cur
    if tc not in came_from:
        return tx, ty
    path = []
    node = tc
    while node and node != sc:
        path.append(node)
        node = came_from.get(node)
    if not path:
        return tx, ty
    next_cell = path[-1]
    wx, wy = _cell_world(*next_cell)
    return float(wx), float(wy)

# ==========================================
# BFS CHO NGƯỜI CHƠI → TÌM XU GẦN NHẤT
# ==========================================
def bfs_find_nearest_coin(px, py, coins_group):
    """BFS tìm xu gần nhất từ vị trí người chơi.
    Trả về coin sprite hoặc None nếu không có xu nào."""
    if _pf_blocked is None or not coins_group:
        return None
    sc = _cell(px, py)
    from collections import deque
    # Lấy tập ô chứa xu
    coin_cells = {}
    for coin in coins_group:
        cc = _cell(coin.rect.centerx, coin.rect.centery)
        if cc not in coin_cells:
            coin_cells[cc] = coin
    if not coin_cells:
        return None
    queue = deque([(sc, 0)])
    visited = {sc}
    while queue:
        cur, dist = queue.popleft()
        if cur in coin_cells:
            return coin_cells[cur]
        if dist > 80:  # giới hạn tìm kiếm
            break
        for nb in _pf_neighbors(*cur):
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, dist + 1))
    # Fallback: trả về xu gần nhất theo khoảng cách Euclidean
    nearest = min(coins_group, key=lambda c: math.hypot(c.rect.centerx - px, c.rect.centery - py), default=None)
    return nearest

# ==========================================
# LỚP ZOMBIE
# ==========================================
class Zombie(pygame.sprite.Sprite):
    # Danh sách thuật toán xoay vòng cho zombie thường
    _ZOMBIE_ALGO_POOL = [
        {"name": "DFS",       "color": (100, 255, 150)},  # xanh lá nhạt
        {"name": "A*",        "color": (255, 220,  80)},  # vàng
        {"name": "Heuristic", "color": (255, 140, 255)},  # tím nhạt
        {"name": "DFS",       "color": (100, 255, 150)},  # xen kẽ
    ]
    _zombie_algo_counter = 0

    def __init__(self, x, y, speed):
        super().__init__()
        # Gán thuật toán theo kiểu round-robin
        algo = Zombie._ZOMBIE_ALGO_POOL[Zombie._zombie_algo_counter % len(Zombie._ZOMBIE_ALGO_POOL)]
        Zombie._zombie_algo_counter += 1
        self.algo_name  = algo["name"]
        self.algo_color = algo["color"]

        self.animations = load_spritesheet("zombie.jpg")
        self.current_direction = "down"
        self.frame_index = 0
        self.image = self.animations[self.current_direction][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed  
        self.max_hp = 100
        self.hp = 100
        self.gold_reward = 40
        
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.move_buffer = [0, 0]

        # Pathfinding cache – tính lại mỗi N frame
        self._pf_timer = random.randint(0, 20)  # offset ngẫu nhiên để không tính cùng lúc
        self._pf_interval = 20   # frames giữa 2 lần tính đường
        self._pf_target = None   # (nx, ny) world coords bước kế tiếp

    def _compute_next_step(self, tx, ty):
        """Gọi đúng thuật toán theo self.algo_name."""
        if self.algo_name == "DFS":
            return dfs_next_step(self.pos_x, self.pos_y, tx, ty, id(self))
        elif self.algo_name == "A*":
            return astar_next_step(self.pos_x, self.pos_y, tx, ty)
        elif self.algo_name == "Heuristic":
            return heuristic_next_step(self.pos_x, self.pos_y, tx, ty)
        else:
            return float(tx), float(ty)

    def update(self, player_rect, obstacles):
        tx = float(player_rect.centerx)
        ty = float(player_rect.centery)

        # Cập nhật pathfinding theo chu kỳ (tránh tính mỗi frame)
        self._pf_timer += 1
        dist_to_player = math.hypot(tx - self.pos_x, ty - self.pos_y)
        if self._pf_timer >= self._pf_interval or self._pf_target is None:
            self._pf_timer = 0
            if dist_to_player < _PF_CELL * 2:
                # Rất gần: đi thẳng
                self._pf_target = (tx, ty)
            else:
                self._pf_target = self._compute_next_step(tx, ty)

        # Di chuyển về phía _pf_target
        nx, ny = self._pf_target
        dx = nx - self.pos_x
        dy = ny - self.pos_y
        distance = math.hypot(dx, dy)
        
        if distance > 2:
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.move_buffer = [move_x, move_y]
        else:
            # Đã đến waypoint, tính lại ngay
            self._pf_target = None
            self._pf_timer = self._pf_interval
        
        old_pos_x = self.pos_x
        old_pos_y = self.pos_y
        
        new_x = self.pos_x + self.move_buffer[0]
        new_y = self.pos_y + self.move_buffer[1]
        
        # X
        self.rect.x = new_x
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        for block in collision_list:
            if self.move_buffer[0] > 0:
                self.rect.right = block.rect.left
            elif self.move_buffer[0] < 0:
                self.rect.left = block.rect.right
        self.pos_x = self.rect.x
        
        # Y
        self.rect.y = new_y
        collision_list = pygame.sprite.spritecollide(self, obstacles, False)
        for block in collision_list:
            if self.move_buffer[1] > 0:
                self.rect.bottom = block.rect.top
            elif self.move_buffer[1] < 0:
                self.rect.top = block.rect.bottom
        self.pos_y = self.rect.y
        
        # Xử lý kẹt góc tường – nếu không di chuyển được, thử trượt theo các hướng khác
        if not hasattr(self, 'stuck_timer'):
            self.stuck_timer = 0
        moved = abs(self.pos_x - old_pos_x) > 0.05 or abs(self.pos_y - old_pos_y) > 0.05
        if not moved:
            self.stuck_timer += 1
            # Reset pathfinding ngay lập tức khi kẹt
            self._pf_target = None
            self._pf_timer = self._pf_interval
            if self.stuck_timer > 5:
                # Thử nhiều góc thoát hơn với khoảng cách lớn hơn
                escaped = False
                for angle in [90, -90, 45, -45, 135, -135, 180, 0]:
                    rad = math.radians(angle)
                    for dist_mult in [3, 5, 8]:
                        test_x = self.pos_x + math.cos(rad) * self.speed * dist_mult
                        test_y = self.pos_y + math.sin(rad) * self.speed * dist_mult
                        # Đảm bảo không ra ngoài biên map
                        test_x = max(STREET_WIDTH + 5, min(test_x, WORLD_WIDTH - STREET_WIDTH - 5))
                        test_y = max(STREET_WIDTH + 5, min(test_y, WORLD_HEIGHT - STREET_WIDTH - 5))
                        self.rect.x = int(test_x)
                        self.rect.y = int(test_y)
                        hit = pygame.sprite.spritecollide(self, obstacles, False)
                        if not hit:
                            self.pos_x = test_x
                            self.pos_y = test_y
                            self.rect.x = int(self.pos_x)
                            self.rect.y = int(self.pos_y)
                            self.stuck_timer = 0
                            escaped = True
                            break
                    if escaped:
                        break
                if not escaped:
                    # Snap ra đường gần nhất nếu hoàn toàn không thoát được
                    snap_x = (int(self.pos_x) // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                    snap_y = (int(self.pos_y) // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                    self.pos_x = float(snap_x)
                    self.pos_y = float(snap_y)
                    self.rect.x = int(self.pos_x)
                    self.rect.y = int(self.pos_y)
                    self.stuck_timer = 0
        else:
            self.stuck_timer = 0
        
        # Animation direction
        if abs(self.move_buffer[0]) > abs(self.move_buffer[1]):
            self.current_direction = "right" if self.move_buffer[0] > 0 else "left"
        else:
            self.current_direction = "down" if self.move_buffer[1] > 0 else "up"
        
        if abs(self.move_buffer[0]) > 0.1 or abs(self.move_buffer[1]) > 0.1:
            self.frame_index += 0.08
            if self.frame_index >= len(self.animations[self.current_direction]):
                self.frame_index = 0
            self.image = self.animations[self.current_direction][int(self.frame_index)]
        else:
            self.image = self.animations[self.current_direction][0]

    def draw_hp_bar(self, surface, camera):
        bar_width, bar_height = 36, 4
        bar_x = (self.rect.centerx - camera.x) - (bar_width // 2)
        bar_y = (self.rect.top - camera.y) - 8
        hp_pct = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * hp_pct)
        pygame.draw.rect(surface, RED,   (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, fill_width, bar_height))

        # === Hiện tên thuật toán trên đầu zombie ===
        algo_font = pygame.font.SysFont("Arial", 9, bold=True)
        # Nền mờ để dễ đọc
        algo_surf  = algo_font.render(self.algo_name, True, self.algo_color)
        algo_w, algo_h = algo_surf.get_size()
        algo_x = (self.rect.centerx - camera.x) - algo_w // 2
        algo_y = bar_y - algo_h - 2
        # Vẽ nền tối nhỏ phía sau chữ
        bg_surf = pygame.Surface((algo_w + 4, algo_h + 2), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 140))
        surface.blit(bg_surf, (algo_x - 2, algo_y - 1))
        surface.blit(algo_surf, (algo_x, algo_y))

# ==========================================
# HIỆU ỨNG VỤ NỔ
# ==========================================
class ExplosionEffect(pygame.sprite.Sprite):
    """Hiệu ứng vụ nổ visual - tự hủy sau vài frame."""
    def __init__(self, cx, cy, radius=80):
        super().__init__()
        self.radius = radius
        self.max_radius = radius
        self.lifetime = 18  # frames
        self.age = 0
        size = radius * 2 + 4
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(cx, cy))
        self._cx = cx
        self._cy = cy
        self._redraw()

    def _redraw(self):
        self.image.fill((0, 0, 0, 0))
        size = self.radius * 2 + 4
        # Tỉ lệ fade
        t = 1.0 - (self.age / self.lifetime)
        alpha_outer = int(180 * t)
        alpha_inner = int(220 * t)
        cx = cy = self.radius + 2
        # Vòng ngoài cam
        pygame.draw.circle(self.image, (255, 120, 0, alpha_outer), (cx, cy), self.radius)
        # Vòng giữa vàng
        pygame.draw.circle(self.image, (255, 230, 0, alpha_inner), (cx, cy), max(2, int(self.radius * 0.6)))
        # Tâm trắng
        pygame.draw.circle(self.image, (255, 255, 220, int(255 * t)), (cx, cy), max(2, int(self.radius * 0.25)))

    def update(self, *args):
        self.age += 1
        # Thu nhỏ dần
        self.radius = int(self.max_radius * (1.0 - self.age / self.lifetime * 0.3))
        if self.age >= self.lifetime:
            self.kill()
        else:
            self._redraw()

# ==========================================
# ZOMBIE NỔ (Exploder)
# ==========================================
class ZombieExploder(Zombie):
    """Zombie nổ: khi chết phát nổ gây sát thương vùng. Dùng A* tìm đường."""
    _ALGO = {"name": "A*", "color": (255, 100, 50)}

    def __init__(self, x, y, speed=None):
        spd = speed if speed else random.uniform(0.8, 1.2)
        super().__init__(x, y, spd)
        self.algo_name  = "A*"
        self.algo_color = (255, 180, 0)
        self.max_hp = 100
        self.hp = 100
        self.gold_reward = 50
        self.explode_radius = 90
        self.explode_damage = 40
        # Tô màu đỏ cam nhận dạng
        tinted = self.image.copy()
        tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint.fill((255, 80, 0, 80))
        tinted.blit(tint, (0, 0))
        self.base_tinted = tinted
        self.image = tinted

    def draw_hp_bar(self, surface, camera):
        # Vẽ HP bar màu cam
        bar_width, bar_height = 36, 4
        bar_x = (self.rect.centerx - camera.x) - (bar_width // 2)
        bar_y = (self.rect.top - camera.y) - 8
        hp_pct = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * hp_pct)
        pygame.draw.rect(surface, (80, 0, 0),   (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (255, 120, 0), (bar_x, bar_y, fill_width, bar_height))
        # Nhãn A* + icon 💥
        algo_font = pygame.font.SysFont("Arial", 9, bold=True)
        algo_surf = algo_font.render("A* 💥", True, (255, 180, 0))
        ax = (self.rect.centerx - camera.x) - algo_surf.get_width() // 2
        ay = bar_y - algo_surf.get_height() - 2
        bg = pygame.Surface((algo_surf.get_width() + 4, algo_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (ax - 2, ay - 1))
        surface.blit(algo_surf, (ax, ay))

# ==========================================
# ZOMBIE TRÂU BÒ (Tank)
# ==========================================
class ZombieTank(Zombie):
    """Zombie trâu bò: máu cao, chậm, to."""
    def __init__(self, x, y, speed=None):
        spd = speed if speed else random.uniform(0.4, 0.7)
        super().__init__(x, y, spd)
        self.algo_name  = "DFS"
        self.algo_color = (100, 200, 100)
        # Scale lớn hơn
        self.animations = load_spritesheet("zombie.jpg", target_size=(80, 80))
        self.image = self.animations[self.current_direction][0]
        # Tô màu xanh lá nhận dạng
        tinted = self.image.copy()
        tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint.fill((0, 180, 0, 70))
        tinted.blit(tint, (0, 0))
        self.image = tinted
        self.rect = self.image.get_rect(center=(x + 32, y + 32))
        self.max_hp = 220
        self.hp = 220
        self.gold_reward = 50
        self.damage_mult = 2.0  # đánh đau hơn

    def draw_hp_bar(self, surface, camera):
        bar_width, bar_height = 48, 5
        bar_x = (self.rect.centerx - camera.x) - (bar_width // 2)
        bar_y = (self.rect.top - camera.y) - 9
        hp_pct = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * hp_pct)
        pygame.draw.rect(surface, (0, 40, 0),   (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (50, 220, 50), (bar_x, bar_y, fill_width, bar_height))
        algo_font = pygame.font.SysFont("Arial", 9, bold=True)
        algo_surf = algo_font.render("DFS 🛡", True, (100, 255, 100))
        ax = (self.rect.centerx - camera.x) - algo_surf.get_width() // 2
        ay = bar_y - algo_surf.get_height() - 2
        bg = pygame.Surface((algo_surf.get_width() + 4, algo_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (ax - 2, ay - 1))
        surface.blit(algo_surf, (ax, ay))

# ==========================================
# ZOMBIE CHẠY NHANH (Speeder)
# ==========================================
class ZombieSpeeder(Zombie):
    """Zombie chạy nhanh: HP thấp nhưng rất nhanh."""
    def __init__(self, x, y, speed=None):
        spd = speed if speed else random.uniform(2.5, 3.5)
        super().__init__(x, y, spd)
        self.algo_name  = "Heuristic"
        self.algo_color = (200, 100, 255)
        # Nhỏ hơn bình thường
        self.animations = load_spritesheet("zombie.jpg", target_size=(38, 38))
        self.image = self.animations[self.current_direction][0]
        # Tô màu tím nhận dạng
        tinted = self.image.copy()
        tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint.fill((180, 0, 255, 90))
        tinted.blit(tint, (0, 0))
        self.image = tinted
        self.rect = self.image.get_rect(center=(x, y))
        self.max_hp = 100
        self.hp = 100
        self.gold_reward = 50

    def draw_hp_bar(self, surface, camera):
        bar_width, bar_height = 26, 3
        bar_x = (self.rect.centerx - camera.x) - (bar_width // 2)
        bar_y = (self.rect.top - camera.y) - 7
        hp_pct = max(0, self.hp / self.max_hp)
        fill_width = int(bar_width * hp_pct)
        pygame.draw.rect(surface, (40, 0, 60),   (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, (220, 80, 255), (bar_x, bar_y, fill_width, bar_height))
        algo_font = pygame.font.SysFont("Arial", 9, bold=True)
        algo_surf = algo_font.render("H* ⚡", True, (200, 100, 255))
        ax = (self.rect.centerx - camera.x) - algo_surf.get_width() // 2
        ay = bar_y - algo_surf.get_height() - 2
        bg = pygame.Surface((algo_surf.get_width() + 4, algo_surf.get_height() + 2), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 140))
        surface.blit(bg, (ax - 2, ay - 1))
        surface.blit(algo_surf, (ax, ay))

# ==========================================
# LỚP BOSS ZOMBIE
# ==========================================
class BossZombie(pygame.sprite.Sprite):
    # Boss dùng xoay vòng giữa A* và Heuristic (thuật toán nặng hơn)
    _BOSS_ALGOS = [
        {"name": "A* Path",    "color": (255, 100, 255)},
        {"name": "Heuristic",  "color": (255, 200,  60)},
    ]
    _boss_tick = 0  # dùng để chớp nháy tên thuật toán

    def __init__(self, x, y):
        super().__init__()
        self.algo_index = 0
        self.algo_switch_timer = 0
        self.algo_switch_interval = 180

        self.animations = load_spritesheet("zombie.jpg", target_size=(90, 90))
        self.current_direction = "down"
        self.frame_index = 0
        self.image = self.animations[self.current_direction][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.speed = 4
        self.max_hp = 10000
        self.hp = 10000
        self.gold_reward = 500
        
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.move_buffer = [0, 0]
        self.corner_slide_timer = 0

        # ── KỸ NĂNG BOSS ──────────────────────────────────────
        # Skill 1: Đập xuống → vụ nổ (Groundslam)
        self.slam_cooldown     = 300   # frames (~5s)
        self.slam_timer        = 150   # bắt đầu nhanh hơn lần đầu
        self.slam_radius       = 130
        self.slam_damage       = 60
        self.is_slamming       = False
        self.slam_anim_timer   = 0
        self.slam_anim_frames  = 20   # frames rung trước khi nổ
        self.pending_explosions = []   # list (cx,cy) chờ nổ

        # Skill 2: Triệu hồi zombie đặc biệt (Summon)
        self.summon_cooldown   = 420   # frames (~7s)
        self.summon_timer      = 200
        self.summon_count      = 4    # số zombie triệu hồi mỗi lần
        self.is_summoning      = False
        self.summon_anim_timer = 0
        self.summon_anim_frames = 30
        self.pending_summons   = []   # sẽ được main loop xử lý

        # Flash effect khi dùng skill
        self.flash_timer = 0
        self.flash_color = (255, 255, 255)

    def _collides(self, rx, ry, obstacles):
        """Kiểm tra Rect tại (rx,ry) có va chạm obstacle nào không."""
        test = self.rect.copy()
        test.x = int(rx)
        test.y = int(ry)
        obs_rects = [b.rect for b in obstacles]
        return test.collidelist(obs_rects) != -1

    def update(self, player_rect, obstacles):
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        distance = math.hypot(dx, dy)
        
        old_pos = (self.pos_x, self.pos_y)
        
        if distance > 0:
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.move_buffer = [move_x, move_y]
        
        new_x = self.pos_x + self.move_buffer[0]
        new_y = self.pos_y + self.move_buffer[1]
        
        if not self._collides(new_x, new_y, obstacles):
            self.pos_x = new_x
            self.pos_y = new_y
        else:
            # X
            if not self._collides(new_x, self.pos_y, obstacles):
                self.pos_x = new_x
            else:
                step_x = self.move_buffer[0] * 0.5
                for _ in range(4):
                    temp_x = self.pos_x + step_x
                    if not self._collides(temp_x, self.pos_y, obstacles):
                        self.pos_x = temp_x
                        break
                    step_x *= 0.5
            
            # Y
            if not self._collides(self.pos_x, new_y, obstacles):
                self.pos_y = new_y
            else:
                step_y = self.move_buffer[1] * 0.5
                for _ in range(4):
                    temp_y = self.pos_y + step_y
                    if not self._collides(self.pos_x, temp_y, obstacles):
                        self.pos_y = temp_y
                        break
                    step_y *= 0.5
        
        # Xử lý kẹt góc
        if abs(old_pos[0] - self.pos_x) < 0.1 and abs(old_pos[1] - self.pos_y) < 0.1:
            self.corner_slide_timer += 1
            if self.corner_slide_timer > 10:
                for angle in [45, -45, 90, -90, 135, -135]:
                    rad = math.radians(angle)
                    escape_x = self.pos_x + math.cos(rad) * self.speed
                    escape_y = self.pos_y + math.sin(rad) * self.speed
                    if not self._collides(escape_x, escape_y, obstacles):
                        self.pos_x = escape_x
                        self.pos_y = escape_y
                        self.corner_slide_timer = 0
                        break
        else:
            self.corner_slide_timer = 0
        
        self.rect.x = self.pos_x
        self.rect.y = self.pos_y
        
        if abs(self.move_buffer[0]) > abs(self.move_buffer[1]):
            self.current_direction = "right" if self.move_buffer[0] > 0 else "left"
        else:
            self.current_direction = "down" if self.move_buffer[1] > 0 else "up"
        
        if abs(self.move_buffer[0]) > 0.1 or abs(self.move_buffer[1]) > 0.1:
            self.frame_index += 0.06
            if self.frame_index >= len(self.animations[self.current_direction]):
                self.frame_index = 0
            self.image = self.animations[self.current_direction][int(self.frame_index)]
        else:
            self.image = self.animations[self.current_direction][0]

        # Chuyển đổi thuật toán theo thời gian (hiệu ứng "đang tính toán")
        self.algo_switch_timer += 1
        if self.algo_switch_timer >= self.algo_switch_interval:
            self.algo_index = (self.algo_index + 1) % len(BossZombie._BOSS_ALGOS)
            self.algo_switch_timer = 0

        # ── SKILL 1: GROUNDSLAM ──────────────────────────────
        if not self.is_slamming:
            self.slam_timer += 1
            if self.slam_timer >= self.slam_cooldown:
                self.is_slamming = True
                self.slam_anim_timer = 0
                self.slam_timer = 0
        else:
            self.slam_anim_timer += 1
            if self.slam_anim_timer >= self.slam_anim_frames:
                # Kích hoạt nổ: 3 vụ nổ quanh boss
                self.is_slamming = False
                for ang in [0, 120, 240]:
                    rad = math.radians(ang)
                    ex = self.pos_x + 50 + math.cos(rad) * 80
                    ey = self.pos_y + 50 + math.sin(rad) * 80
                    self.pending_explosions.append((int(ex), int(ey)))

        # ── SKILL 2: SUMMON ──────────────────────────────────
        if not self.is_summoning:
            self.summon_timer += 1
            if self.summon_timer >= self.summon_cooldown:
                self.is_summoning = True
                self.summon_anim_timer = 0
                self.summon_timer = 0
        else:
            self.summon_anim_timer += 1
            if self.summon_anim_timer >= self.summon_anim_frames:
                self.is_summoning = False
                # Thêm các lệnh triệu hồi để main loop xử lý
                for _ in range(self.summon_count):
                    angle = random.uniform(0, 2 * math.pi)
                    dist  = random.randint(120, 250)
                    sx = int(self.pos_x + math.cos(angle) * dist)
                    sy = int(self.pos_y + math.sin(angle) * dist)
                    sx = max(50, min(sx, WORLD_WIDTH - 50))
                    sy = max(50, min(sy, WORLD_HEIGHT - 50))
                    ztype = random.choice(["exploder", "tank", "speeder"])
                    self.pending_summons.append((sx, sy, ztype))

        # Flash khi đang dùng skill
        if self.is_slamming:
            self.flash_timer = 4
            self.flash_color = (255, 80, 0)
        elif self.is_summoning:
            self.flash_timer = 4
            self.flash_color = (80, 0, 255)
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw_algo_label(self, surface, camera):
        """Vẽ nhãn thuật toán trên đầu boss (gọi sau draw_boss_bar)."""
        algo = BossZombie._BOSS_ALGOS[self.algo_index]
        algo_name  = algo["name"]
        algo_color = algo["color"]

        # Font lớn hơn zombie thường vì boss to hơn
        algo_font = pygame.font.SysFont("Arial", 11, bold=True)
        algo_surf  = algo_font.render(f"[ {algo_name} ]", True, algo_color)
        algo_w, algo_h = algo_surf.get_size()

        scr_cx = int(self.rect.centerx - camera.x)
        scr_ty = int(self.rect.top    - camera.y)
        algo_x = scr_cx - algo_w // 2
        algo_y = scr_ty - algo_h - 4

        # Nền viền mờ
        bg_surf = pygame.Surface((algo_w + 8, algo_h + 4), pygame.SRCALPHA)
        bg_surf.fill((0, 0, 0, 160))
        pygame.draw.rect(bg_surf, algo_color, (0, 0, algo_w + 8, algo_h + 4), 1)
        surface.blit(bg_surf, (algo_x - 4, algo_y - 2))
        surface.blit(algo_surf, (algo_x, algo_y))

    def draw_boss_bar(self, surface):
        bx, by, bw, bh = SCREEN_WIDTH // 2 - 250, 15, 500, 20
        hp_pct = max(0, self.hp / self.max_hp)
        fill_w = int(bw * hp_pct)
        
        # Đổi màu thanh HP theo phần trăm
        if hp_pct > 0.6:
            bar_col = (180, 0, 0)
        elif hp_pct > 0.3:
            bar_col = (200, 100, 0)
        else:
            bar_col = (220, 0, 180)

        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bw, bh), border_radius=5)
        pygame.draw.rect(surface, bar_col,   (bx, by, fill_w, bh), border_radius=5)
        pygame.draw.rect(surface, WHITE,     (bx, by, bw, bh), 2, border_radius=5)
        
        algo = BossZombie._BOSS_ALGOS[self.algo_index]
        lbl_font = get_font("Arial", 14, bold=True)
        lbl_text = lbl_font.render(
            f"TYRANT BOSS  [{algo['name']}]  HP: {int(self.hp)}/{self.max_hp}",
            True, WHITE)
        surface.blit(lbl_text, (SCREEN_WIDTH // 2 - lbl_text.get_width() // 2, by + 2))

        # Cooldown bars bên dưới thanh HP
        skill_font = pygame.font.SysFont("Arial", 10, bold=True)
        # Slam cooldown
        slam_pct = min(1.0, self.slam_timer / self.slam_cooldown)
        slam_label = "💥SLAM" if not self.is_slamming else "💥 !!!"
        slam_col   = (255, 80, 0) if self.is_slamming else (200, 120, 0)
        pygame.draw.rect(surface, DARK_GRAY,  (bx, by + bh + 3, 120, 7), border_radius=3)
        pygame.draw.rect(surface, slam_col,   (bx, by + bh + 3, int(120 * slam_pct), 7), border_radius=3)
        s1 = skill_font.render(slam_label, True, (255, 180, 0))
        surface.blit(s1, (bx, by + bh + 12))
        # Summon cooldown
        summ_pct = min(1.0, self.summon_timer / self.summon_cooldown)
        summ_label = "👾SUMMON" if not self.is_summoning else "👾 !!!"
        summ_col   = (80, 0, 255) if self.is_summoning else (100, 60, 200)
        pygame.draw.rect(surface, DARK_GRAY,  (bx + 140, by + bh + 3, 120, 7), border_radius=3)
        pygame.draw.rect(surface, summ_col,   (bx + 140, by + bh + 3, int(120 * summ_pct), 7), border_radius=3)
        s2 = skill_font.render(summ_label, True, (160, 100, 255))
        surface.blit(s2, (bx + 140, by + bh + 12))

# ==========================================
# BOSS MÀN 1: ZOMBIE TRÙM ĐƠN GIẢN (cấp độ Dễ)
# ==========================================
class BossZombieLv1(pygame.sprite.Sprite):
    """Boss màn 1 – Chậm, HP thấp, chỉ có 1 skill: GROUNDSLAM nhỏ."""
    def __init__(self, x, y):
        super().__init__()
        self.animations = load_spritesheet("zombie.jpg", target_size=(90, 90))
        self.current_direction = "down"
        self.frame_index = 0
        self.image = self.animations[self.current_direction][0]
        tinted = self.image.copy()
        tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint.fill((255, 100, 0, 100))
        tinted.blit(tint, (0, 0))
        self.image = tinted
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.speed = 3
        self.max_hp = 5000
        self.hp = 5000
        self.gold_reward = 200

        self.pos_x = float(x)
        self.pos_y = float(y)
        self.move_buffer = [0, 0]
        self.corner_slide_timer = 0

        # Skill duy nhất: GroundSlam yếu
        self.slam_cooldown    = 360
        self.slam_timer       = 180
        self.slam_radius      = 90
        self.slam_damage      = 30
        self.is_slamming      = False
        self.slam_anim_timer  = 0
        self.slam_anim_frames = 20
        self.pending_explosions = []

        self.is_summoning = False  # không có skill này nhưng main loop kiểm tra
        self.pending_summons = []

        self.flash_timer = 0
        self.flash_color = (255, 255, 255)

    def _collides(self, rx, ry, obstacles):
        test = self.rect.copy()
        test.x = int(rx)
        test.y = int(ry)
        return test.collidelist([b.rect for b in obstacles]) != -1

    def update(self, player_rect, obstacles):
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        distance = math.hypot(dx, dy)
        old_pos = (self.pos_x, self.pos_y)

        if distance > 0:
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.move_buffer = [move_x, move_y]

        new_x = self.pos_x + self.move_buffer[0]
        new_y = self.pos_y + self.move_buffer[1]

        if not self._collides(new_x, new_y, obstacles):
            self.pos_x = new_x
            self.pos_y = new_y
        else:
            if not self._collides(new_x, self.pos_y, obstacles):
                self.pos_x = new_x
            if not self._collides(self.pos_x, new_y, obstacles):
                self.pos_y = new_y

        if abs(old_pos[0] - self.pos_x) < 0.1 and abs(old_pos[1] - self.pos_y) < 0.1:
            self.corner_slide_timer += 1
            if self.corner_slide_timer > 10:
                for angle in [45, -45, 90, -90, 135, -135]:
                    rad = math.radians(angle)
                    ex = self.pos_x + math.cos(rad) * self.speed
                    ey = self.pos_y + math.sin(rad) * self.speed
                    if not self._collides(ex, ey, obstacles):
                        self.pos_x = ex
                        self.pos_y = ey
                        self.corner_slide_timer = 0
                        break
        else:
            self.corner_slide_timer = 0

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if abs(self.move_buffer[0]) > abs(self.move_buffer[1]):
            self.current_direction = "right" if self.move_buffer[0] > 0 else "left"
        else:
            self.current_direction = "down" if self.move_buffer[1] > 0 else "up"

        if abs(self.move_buffer[0]) > 0.1 or abs(self.move_buffer[1]) > 0.1:
            self.frame_index += 0.06
            if self.frame_index >= len(self.animations[self.current_direction]):
                self.frame_index = 0
            self.image = self.animations[self.current_direction][int(self.frame_index)]

        # Skill: GroundSlam
        if not self.is_slamming:
            self.slam_timer += 1
            if self.slam_timer >= self.slam_cooldown:
                self.is_slamming = True
                self.slam_anim_timer = 0
                self.slam_timer = 0
        else:
            self.slam_anim_timer += 1
            if self.slam_anim_timer >= self.slam_anim_frames:
                self.is_slamming = False
                for ang in [0, 180]:
                    rad = math.radians(ang)
                    ex = self.pos_x + 36 + math.cos(rad) * 60
                    ey = self.pos_y + 36 + math.sin(rad) * 60
                    self.pending_explosions.append((int(ex), int(ey)))

        if self.is_slamming:
            self.flash_timer = 4
            self.flash_color = (255, 80, 0)
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw_boss_bar(self, surface):
        bx, by, bw, bh = SCREEN_WIDTH // 2 - 200, 15, 400, 20
        hp_pct = max(0, self.hp / self.max_hp)
        fill_w = int(bw * hp_pct)
        bar_col = (180, 80, 0) if hp_pct > 0.4 else (220, 30, 30)
        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bw, bh), border_radius=5)
        pygame.draw.rect(surface, bar_col,   (bx, by, fill_w, bh), border_radius=5)
        pygame.draw.rect(surface, WHITE,     (bx, by, bw, bh), 2, border_radius=5)
        lbl_font = get_font("Arial", 14, bold=True)
        lbl = lbl_font.render(f"BOSS MAN 1 - ALPHA  HP: {int(self.hp)}/{self.max_hp}", True, WHITE)
        surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, by + 2))
        # Slam cooldown bar
        skill_font = pygame.font.SysFont("Arial", 10, bold=True)
        slam_pct = min(1.0, self.slam_timer / self.slam_cooldown)
        slam_col = (255, 80, 0) if self.is_slamming else (200, 120, 0)
        pygame.draw.rect(surface, DARK_GRAY, (bx, by + bh + 3, 120, 7), border_radius=3)
        pygame.draw.rect(surface, slam_col,  (bx, by + bh + 3, int(120 * slam_pct), 7), border_radius=3)
        s1 = skill_font.render("💥SLAM" if not self.is_slamming else "💥 !!!", True, (255, 180, 0))
        surface.blit(s1, (bx, by + bh + 12))

    def draw_algo_label(self, surface, camera):
        algo_font = pygame.font.SysFont("Arial", 11, bold=True)
        algo_surf = algo_font.render("[ ALPHA BOSS ]", True, (255, 140, 0))
        scr_cx = int(self.rect.centerx - camera.x)
        scr_ty = int(self.rect.top - camera.y)
        algo_x = scr_cx - algo_surf.get_width() // 2
        algo_y = scr_ty - algo_surf.get_height() - 4
        bg = pygame.Surface((algo_surf.get_width() + 8, algo_surf.get_height() + 4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (algo_x - 4, algo_y - 2))
        surface.blit(algo_surf, (algo_x, algo_y))


# ==========================================
# BOSS MÀN 2: ZOMBIE TRÙM TRUNG BÌNH (cấp độ Khó)
# ==========================================
class BossZombieLv2(pygame.sprite.Sprite):
    """Boss màn 2 – Nhanh hơn, HP cao hơn, có GroundSlam + triệu hồi 2 zombie."""
    def __init__(self, x, y):
        super().__init__()
        self.animations = load_spritesheet("zombie.jpg", target_size=(90, 90))
        self.current_direction = "down"
        self.frame_index = 0
        self.image = self.animations[self.current_direction][0]
        # Tô màu xanh lam để phân biệt
        tinted = self.image.copy()
        tint = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
        tint.fill((0, 120, 255, 110))
        tinted.blit(tint, (0, 0))
        self.image = tinted
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self.speed = 4
        self.max_hp = 8000
        self.hp = 8000
        self.gold_reward = 350

        self.pos_x = float(x)
        self.pos_y = float(y)
        self.move_buffer = [0, 0]
        self.corner_slide_timer = 0

        # Skill 1: GroundSlam trung bình
        self.slam_cooldown    = 300
        self.slam_timer       = 150
        self.slam_radius      = 110
        self.slam_damage      = 45
        self.is_slamming      = False
        self.slam_anim_timer  = 0
        self.slam_anim_frames = 20
        self.pending_explosions = []

        # Skill 2: Summon 2 zombie thường
        self.summon_cooldown    = 480
        self.summon_timer       = 240
        self.summon_count       = 2
        self.is_summoning       = False
        self.summon_anim_timer  = 0
        self.summon_anim_frames = 30
        self.pending_summons    = []

        self.flash_timer = 0
        self.flash_color = (255, 255, 255)

    def _collides(self, rx, ry, obstacles):
        test = self.rect.copy()
        test.x = int(rx)
        test.y = int(ry)
        return test.collidelist([b.rect for b in obstacles]) != -1

    def update(self, player_rect, obstacles):
        dx = player_rect.centerx - self.pos_x
        dy = player_rect.centery - self.pos_y
        distance = math.hypot(dx, dy)
        old_pos = (self.pos_x, self.pos_y)

        if distance > 0:
            move_x = (dx / distance) * self.speed
            move_y = (dy / distance) * self.speed
            self.move_buffer = [move_x, move_y]

        new_x = self.pos_x + self.move_buffer[0]
        new_y = self.pos_y + self.move_buffer[1]

        if not self._collides(new_x, new_y, obstacles):
            self.pos_x = new_x
            self.pos_y = new_y
        else:
            if not self._collides(new_x, self.pos_y, obstacles):
                self.pos_x = new_x
            if not self._collides(self.pos_x, new_y, obstacles):
                self.pos_y = new_y

        if abs(old_pos[0] - self.pos_x) < 0.1 and abs(old_pos[1] - self.pos_y) < 0.1:
            self.corner_slide_timer += 1
            if self.corner_slide_timer > 10:
                for angle in [45, -45, 90, -90, 135, -135]:
                    rad = math.radians(angle)
                    ex = self.pos_x + math.cos(rad) * self.speed
                    ey = self.pos_y + math.sin(rad) * self.speed
                    if not self._collides(ex, ey, obstacles):
                        self.pos_x = ex
                        self.pos_y = ey
                        self.corner_slide_timer = 0
                        break
        else:
            self.corner_slide_timer = 0

        self.rect.x = int(self.pos_x)
        self.rect.y = int(self.pos_y)

        if abs(self.move_buffer[0]) > abs(self.move_buffer[1]):
            self.current_direction = "right" if self.move_buffer[0] > 0 else "left"
        else:
            self.current_direction = "down" if self.move_buffer[1] > 0 else "up"

        if abs(self.move_buffer[0]) > 0.1 or abs(self.move_buffer[1]) > 0.1:
            self.frame_index += 0.07
            if self.frame_index >= len(self.animations[self.current_direction]):
                self.frame_index = 0
            self.image = self.animations[self.current_direction][int(self.frame_index)]

        # Skill 1: GroundSlam
        if not self.is_slamming:
            self.slam_timer += 1
            if self.slam_timer >= self.slam_cooldown:
                self.is_slamming = True
                self.slam_anim_timer = 0
                self.slam_timer = 0
        else:
            self.slam_anim_timer += 1
            if self.slam_anim_timer >= self.slam_anim_frames:
                self.is_slamming = False
                for ang in [0, 120, 240]:
                    rad = math.radians(ang)
                    ex = self.pos_x + 43 + math.cos(rad) * 70
                    ey = self.pos_y + 43 + math.sin(rad) * 70
                    self.pending_explosions.append((int(ex), int(ey)))

        # Skill 2: Summon
        if not self.is_summoning:
            self.summon_timer += 1
            if self.summon_timer >= self.summon_cooldown:
                self.is_summoning = True
                self.summon_anim_timer = 0
                self.summon_timer = 0
        else:
            self.summon_anim_timer += 1
            if self.summon_anim_timer >= self.summon_anim_frames:
                self.is_summoning = False
                for _ in range(self.summon_count):
                    angle = random.uniform(0, 2 * math.pi)
                    dist  = random.randint(100, 200)
                    sx = int(self.pos_x + math.cos(angle) * dist)
                    sy = int(self.pos_y + math.sin(angle) * dist)
                    sx = max(50, min(sx, WORLD_WIDTH - 50))
                    sy = max(50, min(sy, WORLD_HEIGHT - 50))
                    ztype = random.choice(["speeder", "tank"])
                    self.pending_summons.append((sx, sy, ztype))

        if self.is_slamming:
            self.flash_timer = 4
            self.flash_color = (255, 80, 0)
        elif self.is_summoning:
            self.flash_timer = 4
            self.flash_color = (0, 100, 255)
        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw_boss_bar(self, surface):
        bx, by, bw, bh = SCREEN_WIDTH // 2 - 220, 15, 440, 20
        hp_pct = max(0, self.hp / self.max_hp)
        fill_w = int(bw * hp_pct)
        bar_col = (0, 100, 200) if hp_pct > 0.4 else (0, 180, 255)
        pygame.draw.rect(surface, DARK_GRAY, (bx, by, bw, bh), border_radius=5)
        pygame.draw.rect(surface, bar_col,   (bx, by, fill_w, bh), border_radius=5)
        pygame.draw.rect(surface, WHITE,     (bx, by, bw, bh), 2, border_radius=5)
        lbl_font = get_font("Arial", 14, bold=True)
        lbl = lbl_font.render(f"BOSS MAN 2 - BETA  HP: {int(self.hp)}/{self.max_hp}", True, WHITE)
        surface.blit(lbl, (SCREEN_WIDTH // 2 - lbl.get_width() // 2, by + 2))
        skill_font = pygame.font.SysFont("Arial", 10, bold=True)
        # Slam bar
        slam_pct = min(1.0, self.slam_timer / self.slam_cooldown)
        slam_col = (255, 80, 0) if self.is_slamming else (200, 120, 0)
        pygame.draw.rect(surface, DARK_GRAY, (bx, by + bh + 3, 120, 7), border_radius=3)
        pygame.draw.rect(surface, slam_col,  (bx, by + bh + 3, int(120 * slam_pct), 7), border_radius=3)
        surface.blit(skill_font.render("💥SLAM" if not self.is_slamming else "💥 !!!", True, (255, 180, 0)), (bx, by + bh + 12))
        # Summon bar
        summ_pct = min(1.0, self.summon_timer / self.summon_cooldown)
        summ_col = (0, 80, 255) if self.is_summoning else (0, 60, 180)
        pygame.draw.rect(surface, DARK_GRAY, (bx + 140, by + bh + 3, 120, 7), border_radius=3)
        pygame.draw.rect(surface, summ_col,  (bx + 140, by + bh + 3, int(120 * summ_pct), 7), border_radius=3)
        surface.blit(skill_font.render("👾SUMMON" if not self.is_summoning else "👾 !!!", True, (80, 160, 255)), (bx + 140, by + bh + 12))

    def draw_algo_label(self, surface, camera):
        algo_font = pygame.font.SysFont("Arial", 11, bold=True)
        algo_surf = algo_font.render("[ BETA BOSS ]", True, (60, 180, 255))
        scr_cx = int(self.rect.centerx - camera.x)
        scr_ty = int(self.rect.top - camera.y)
        algo_x = scr_cx - algo_surf.get_width() // 2
        algo_y = scr_ty - algo_surf.get_height() - 4
        bg = pygame.Surface((algo_surf.get_width() + 8, algo_surf.get_height() + 4), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 160))
        surface.blit(bg, (algo_x - 4, algo_y - 2))
        surface.blit(algo_surf, (algo_x, algo_y))


# ==========================================
# HỆ THỐNG CAMERA
# ==========================================
class Camera:
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.x = 0
        self.y = 0
        self.ground_img = None
        self.tile_w = 64  
        self.tile_h = 64

        possible_files = ["ground.png", "ground.jpg", "ground.jpeg", "manhdat.png", "manhdat.jpg"]
        found_file = None
        
        for filename in possible_files:
            if os.path.exists(filename):
                found_file = filename
                break

        if found_file:
            try:
                self.ground_img = pygame.image.load(found_file).convert_alpha()
                self.tile_w, self.tile_h = self.ground_img.get_size()
            except pygame.error:
                pass

    def apply(self, entity):
        return entity.rect.move(-self.x, -self.y)

    def update(self, target):
        self.x = target.rect.centerx - int(SCREEN_WIDTH / 2)
        self.y = target.rect.centery - int(SCREEN_HEIGHT / 2)
        self.x = max(0, min(self.x, WORLD_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, WORLD_HEIGHT - SCREEN_HEIGHT))

    def draw_world_blocks(self, surface):
        if self.ground_img:
            start_x = (self.x // self.tile_w) * self.tile_w
            start_y = (self.y // self.tile_h) * self.tile_h
            end_x = start_x + SCREEN_WIDTH + self.tile_w
            end_y = start_y + SCREEN_HEIGHT + self.tile_h

            for x in range(start_x, end_x, self.tile_w):
                for y in range(start_y, end_y, self.tile_h):
                    if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT:
                        surface.blit(self.ground_img, (x - self.x, y - self.y))
        else:
            start_x = (self.x // 64) * 64
            start_y = (self.y // 64) * 64
            for x in range(start_x, start_x + SCREEN_WIDTH + 64, 64):
                for y in range(start_y, start_y + SCREEN_HEIGHT + 64, 64):
                    if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT:
                        pygame.draw.rect(surface, BLOCK_GROUND, (x - self.x, y - self.y, 64, 64))
        
        for x in range(0, WORLD_WIDTH, BLOCK_SIZE):
            for y in range(0, WORLD_HEIGHT, BLOCK_SIZE):
                bx = x - self.x
                by = y - self.y
                if -BLOCK_SIZE <= bx <= SCREEN_WIDTH and -BLOCK_SIZE <= by <= SCREEN_HEIGHT:
                    pygame.draw.rect(surface, (32, 42, 32), (bx, by, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_streets(self, surface):
        # Vẽ đường dọc (kể cả mép trái và phải map)
        street_x_positions = list(range(0, WORLD_WIDTH, BLOCK_SIZE)) + [WORLD_WIDTH - STREET_WIDTH]
        for x in street_x_positions:
            street_x = x - self.x
            if -STREET_WIDTH <= street_x <= SCREEN_WIDTH:
                pygame.draw.rect(surface, STREET_COLOR, (street_x, 0, STREET_WIDTH, SCREEN_HEIGHT))
                for y_dash in range(0, SCREEN_HEIGHT + 40, 40):
                    world_y = (y_dash + self.y) // 40 * 40
                    if 0 <= world_y <= WORLD_HEIGHT:
                        pygame.draw.line(surface, WHITE, (street_x + STREET_WIDTH//2, y_dash - (self.y % 40)),
                                         (street_x + STREET_WIDTH//2, y_dash - (self.y % 40) + 20), 2)

        # Vẽ đường ngang (kể cả mép trên và dưới map)
        street_y_positions = list(range(0, WORLD_HEIGHT, BLOCK_SIZE)) + [WORLD_HEIGHT - STREET_WIDTH]
        for y in street_y_positions:
            street_y = y - self.y
            if -STREET_WIDTH <= street_y <= SCREEN_HEIGHT:
                pygame.draw.rect(surface, STREET_COLOR, (0, street_y, SCREEN_WIDTH, STREET_WIDTH))
                for x_dash in range(0, SCREEN_WIDTH + 40, 40):
                    world_x = (x_dash + self.x) // 40 * 40
                    if 0 <= world_x <= WORLD_WIDTH:
                        pygame.draw.line(surface, LINE_YELLOW, (x_dash - (self.x % 40), street_y + STREET_WIDTH//2),
                                         (x_dash - (self.x % 40) + 20, street_y + STREET_WIDTH//2), 2)

    def draw_minimap(self, surface, player, zombies, coins, buildings):
        mm_width, mm_height = 150, 110
        mm_x = SCREEN_WIDTH - mm_width - 15
        mm_y = 15
        
        pygame.draw.rect(surface, (15, 20, 15), (mm_x, mm_y, mm_width, mm_height))
        pygame.draw.rect(surface, WHITE, (mm_x, mm_y, mm_width, mm_height), 1)
        
        scale_x = mm_width / WORLD_WIDTH
        scale_y = mm_height / WORLD_HEIGHT
        
        for b in buildings:
            bx = mm_x + int(b.rect.x * scale_x)
            by = mm_y + int(b.rect.y * scale_y)
            bw = int(b.rect.width * scale_x)
            bh = int(b.rect.height * scale_y)
            pygame.draw.rect(surface, (120, 120, 120), (bx, by, bw, bh))
            
        for coin in coins:
            c_mm_x = mm_x + int(coin.rect.centerx * scale_x)
            c_mm_y = mm_y + int(coin.rect.centery * scale_y)
            if mm_x <= c_mm_x <= mm_x + mm_width and mm_y <= c_mm_y <= mm_y + mm_height:
                pygame.draw.circle(surface, YELLOW, (c_mm_x, c_mm_y), 2)
                
        for zombie in zombies:
            z_mm_x = mm_x + int(zombie.rect.centerx * scale_x)
            z_mm_y = mm_y + int(zombie.rect.centery * scale_y)
            if mm_x <= z_mm_x <= mm_x + mm_width and mm_y <= z_mm_y <= mm_y + mm_height:
                if isinstance(zombie, BossZombie):
                    # Boss màn 3: chấm tím to nhấp nháy
                    pulse = int(math.sin(pygame.time.get_ticks() * 0.008) * 2)
                    boss_r = 7 + pulse
                    pygame.draw.circle(surface, (80, 0, 80), (z_mm_x, z_mm_y), boss_r + 2)
                    pygame.draw.circle(surface, (200, 0, 255), (z_mm_x, z_mm_y), boss_r)
                    pygame.draw.circle(surface, (255, 150, 255), (z_mm_x, z_mm_y), max(2, boss_r - 3))
                elif isinstance(zombie, BossZombieLv2):
                    # Boss màn 2: chấm xanh lam
                    pulse = int(math.sin(pygame.time.get_ticks() * 0.008) * 2)
                    boss_r = 6 + pulse
                    pygame.draw.circle(surface, (0, 40, 120), (z_mm_x, z_mm_y), boss_r + 2)
                    pygame.draw.circle(surface, (0, 100, 255), (z_mm_x, z_mm_y), boss_r)
                elif isinstance(zombie, BossZombieLv1):
                    # Boss màn 1: chấm cam
                    pulse = int(math.sin(pygame.time.get_ticks() * 0.008) * 2)
                    boss_r = 5 + pulse
                    pygame.draw.circle(surface, (120, 50, 0), (z_mm_x, z_mm_y), boss_r + 2)
                    pygame.draw.circle(surface, (255, 130, 0), (z_mm_x, z_mm_y), boss_r)
                else:
                    pygame.draw.circle(surface, RED, (z_mm_x, z_mm_y), 2)
                
        p_mm_x = mm_x + int(player.rect.centerx * scale_x)
        p_mm_y = mm_y + int(player.rect.centery * scale_y)
        pygame.draw.circle(surface, GREEN, (p_mm_x, p_mm_y), 3)

# ==========================================
# CÁC HÀM VẼ MENU (RÚT GỌN DO GIỚI HẠN)
# ==========================================

def draw_lobby_menu(surface, font_title, font_btn, current_lvl):
    surface.fill((8, 12, 8))
    grid_color = (14, 22, 14)
    for gx in range(0, SCREEN_WIDTH, 80):
        pygame.draw.line(surface, grid_color, (gx, 0), (gx, SCREEN_HEIGHT))
    for gy in range(0, SCREEN_HEIGHT, 80):
        pygame.draw.line(surface, grid_color, (0, gy), (SCREEN_WIDTH, gy))

    pygame.draw.line(surface, (0, 160, 50), (60, 170), (SCREEN_WIDTH - 60, 170), 1)

    TOXIC_GREEN = (60, 255, 100)
    ACID_YELLOW = (210, 255, 50)

    font_big = get_font("Arial", 48, bold=True)
    font_sub = get_font("Arial", 22, bold=True)

    title1 = font_big.render("SINH TON", True, TOXIC_GREEN)
    title2 = font_big.render("THANH PHO NHIEM DOC", True, ACID_YELLOW)

    shadow_col = (0, 80, 20)
    title1_sh = font_big.render("SINH TON", True, shadow_col)
    title2_sh = font_big.render("THANH PHO NHIEM DOC", True, shadow_col)
    surface.blit(title1_sh, (SCREEN_WIDTH // 2 - title1.get_width() // 2 + 3, 63))
    surface.blit(title2_sh, (SCREEN_WIDTH // 2 - title2.get_width() // 2 + 3, 113))
    surface.blit(title1, (SCREEN_WIDTH // 2 - title1.get_width() // 2, 60))
    surface.blit(title2, (SCREEN_WIDTH // 2 - title2.get_width() // 2, 110))

    sub_surf = font_sub.render("- He thong sinh ton do thi 3 cap do -", True, (140, 200, 140))
    surface.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 162))

    pygame.draw.line(surface, (0, 160, 50), (60, 185), (SCREEN_WIDTH - 60, 185), 1)

    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    menu_items = [
        {"key": "play_now", "text": ">  CHOI NGAY", "color_idle": (20, 80, 35), "color_hover": (30, 140, 60), "border_idle": (50, 180, 80), "border_hover": (120, 255, 100), "txt_idle": TOXIC_GREEN, "txt_hover": (220, 255, 220)},
        {"key": "level", "text": f"?  MAN: {LEVELS[current_lvl]['name']}", "color_idle": (18, 50, 60), "color_hover": (25, 90, 110), "border_idle": (40, 130, 160), "border_hover": ACID_YELLOW, "txt_idle": (80, 200, 230), "txt_hover": WHITE},
        {"key": "guide", "text": "?  HUONG DAN CHOI", "color_idle": (35, 35, 20), "color_hover": (65, 65, 20), "border_idle": (120, 120, 40), "border_hover": ACID_YELLOW, "txt_idle": (200, 200, 80), "txt_hover": WHITE},
        {"key": "exit", "text": "X  THOAT GAME", "color_idle": (50, 15, 15), "color_hover": (130, 30, 30), "border_idle": (120, 40, 40), "border_hover": (255, 80, 80), "txt_idle": (210, 70, 70), "txt_hover": (255, 180, 180)},
    ]

    start_y = 215
    for item in menu_items:
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 165, start_y, 330, 50)
        hovering = btn_rect.collidepoint(mouse_pos)
        bg_col = item["color_hover"] if hovering else item["color_idle"]
        border_col = item["border_hover"] if hovering else item["border_idle"]
        txt_col = item["txt_hover"] if hovering else item["txt_idle"]
        border_w = 2 if hovering else 1

        pygame.draw.rect(surface, bg_col, btn_rect, border_radius=8)
        pygame.draw.rect(surface, border_col, btn_rect, border_w, border_radius=8)

        if hovering:
            accent_rect = pygame.Rect(btn_rect.x, btn_rect.y + 6, 4, btn_rect.height - 12)
            pygame.draw.rect(surface, border_col, accent_rect, border_radius=2)

        txt_surf = font_btn.render(item["text"], True, txt_col)
        surface.blit(txt_surf, (btn_rect.x + 20, btn_rect.y + (btn_rect.height - txt_surf.get_height()) // 2))
        buttons[item["key"]] = btn_rect
        start_y += 65

    pygame.draw.line(surface, (0, 100, 30), (60, SCREEN_HEIGHT - 40), (SCREEN_WIDTH - 60, SCREEN_HEIGHT - 40), 1)
    ver_surf = get_font("Arial", 13, bold=False).render("v1.0 | Sinh Ton Thanh Pho Nhiem Doc | 3 Man Choi", True, (60, 100, 60))
    surface.blit(ver_surf, (SCREEN_WIDTH // 2 - ver_surf.get_width() // 2, SCREEN_HEIGHT - 28))

    return buttons

def draw_level_menu(surface, font_title, font_btn, current_lvl):
    surface.fill((10, 12, 18))
    grid_col = (15, 18, 28)
    for gx in range(0, SCREEN_WIDTH, 80):
        pygame.draw.line(surface, grid_col, (gx, 0), (gx, SCREEN_HEIGHT))
    for gy in range(0, SCREEN_HEIGHT, 80):
        pygame.draw.line(surface, grid_col, (0, gy), (SCREEN_WIDTH, gy))

    pygame.draw.line(surface, (80, 80, 160), (60, 110), (SCREEN_WIDTH - 60, 110), 1)

    font_big = get_font("Arial", 40, bold=True)
    title_surf = font_big.render("?  CHON MAN CHOI", True, (180, 200, 255))
    sh = font_big.render("?  CHON MAN CHOI", True, (20, 20, 60))
    surface.blit(sh, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + 2, 62))
    surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 60))

    pygame.draw.line(surface, (80, 80, 160), (60, 115), (SCREEN_WIDTH - 60, 115), 1)

    mouse_pos = pygame.mouse.get_pos()
    buttons = {}

    level_styles = {
        1: {"idle_bg": (15, 45, 20), "hover_bg": (25, 90, 40), "idle_border": (40, 160, 70), "hover_border": (100, 255, 130), "idle_txt": (80, 200, 100), "hover_txt": (220, 255, 220), "tag": "DE", "tag_col": (80, 220, 100)},
        2: {"idle_bg": (45, 30, 10), "hover_bg": (100, 60, 10), "idle_border": (160, 100, 30), "hover_border": (255, 180, 60), "idle_txt": (210, 150, 50), "hover_txt": (255, 230, 180), "tag": "KHO", "tag_col": (255, 180, 50)},
        3: {"idle_bg": (45, 10, 10), "hover_bg": (110, 20, 20), "idle_border": (160, 40, 40), "hover_border": (255, 80, 80), "idle_txt": (210, 70, 70), "hover_txt": (255, 200, 200), "tag": "BOSS", "tag_col": (255, 60, 60)},
    }

    start_y = 155
    for lvl_id, cfg in LEVELS.items():
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 200, start_y, 400, 64)
        hovering = btn_rect.collidepoint(mouse_pos)
        is_selected = (lvl_id == current_lvl)
        s = level_styles[lvl_id]

        bg_col = s["hover_bg"] if hovering else s["idle_bg"]
        border_col = s["hover_border"] if (hovering or is_selected) else s["idle_border"]
        txt_col = s["hover_txt"] if hovering else s["idle_txt"]

        pygame.draw.rect(surface, bg_col, btn_rect, border_radius=10)
        pygame.draw.rect(surface, border_col, btn_rect, 2, border_radius=10)

        if hovering or is_selected:
            pygame.draw.rect(surface, border_col, (btn_rect.x, btn_rect.y + 8, 5, btn_rect.height - 16), border_radius=2)

        tag_font = get_font("Arial", 12, bold=True)
        tag_surf = tag_font.render(s["tag"], True, s["tag_col"])
        tag_bg = pygame.Rect(btn_rect.right - tag_surf.get_width() - 20, btn_rect.y + 8, tag_surf.get_width() + 12, 20)
        pygame.draw.rect(surface, (0, 0, 0, 0), tag_bg, border_radius=4)
        pygame.draw.rect(surface, s["tag_col"], tag_bg, 1, border_radius=4)
        surface.blit(tag_surf, (tag_bg.x + 6, tag_bg.y + 3))

        if is_selected:
            sel_font = get_font("Arial", 11, bold=True)
            sel_surf = sel_font.render("? DANG CHON", True, border_col)
            surface.blit(sel_surf, (btn_rect.right - sel_surf.get_width() - 18, btn_rect.bottom - 22))

        txt_surf = font_btn.render(cfg['name'], True, txt_col)
        dur_surf = get_font("Arial", 14, bold=False).render(f"@  {cfg['duration_minutes']} phut sinh ton", True, (160, 160, 180))
        surface.blit(txt_surf, (btn_rect.x + 20, btn_rect.y + 10))
        surface.blit(dur_surf, (btn_rect.x + 20, btn_rect.y + 36))

        buttons[f"lvl_{lvl_id}"] = btn_rect
        start_y += 85

    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, 480, 220, 48)
    hover_back = back_rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, (90, 30, 30) if hover_back else (35, 15, 15), back_rect, border_radius=8)
    pygame.draw.rect(surface, (200, 60, 60) if hover_back else (100, 40, 40), back_rect, 1, border_radius=8)
    back_surf = font_btn.render("? QUAY LAI SANH", True, (220, 120, 120) if hover_back else (160, 80, 80))
    surface.blit(back_surf, (back_rect.x + (back_rect.width - back_surf.get_width()) // 2,
                             back_rect.y + (back_rect.height - back_surf.get_height()) // 2))
    buttons["back"] = back_rect

    return buttons

def draw_guide_menu(surface, font_title, font_text, font_btn):
    surface.fill((10, 14, 10))
    for gx in range(0, SCREEN_WIDTH, 80):
        pygame.draw.line(surface, (14, 20, 14), (gx, 0), (gx, SCREEN_HEIGHT))
    for gy in range(0, SCREEN_HEIGHT, 80):
        pygame.draw.line(surface, (14, 20, 14), (0, gy), (SCREEN_WIDTH, gy))

    pygame.draw.line(surface, (50, 180, 80), (60, 105), (SCREEN_WIDTH - 60, 105), 1)
    font_big = get_font("Arial", 38, bold=True)
    title_surf = font_big.render("?  HUONG DAN CHOI", True, (180, 255, 180))
    sh = font_big.render("?  HUONG DAN CHOI", True, (10, 50, 10))
    surface.blit(sh, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2 + 2, 62))
    surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 60))
    pygame.draw.line(surface, (50, 180, 80), (60, 110), (SCREEN_WIDTH - 60, 110), 1)

    guide_lines = [
        ("move", "W / A / S / D hoac phim mui ten", "Di chuyen nhan vat"),
        ("shoot", "Nhap giu Chuot Trai", "Ban ha Zombie"),
        ("reload", "Phim [ R ]", "Thay dan thu cong"),
        ("swap", "Phim [ Q ]", "Doi sung tuan hoan"),
        ("num", "Phim so [ 1 ] [ 2 ] [ 3 ] [ 4 ]", "Chon nhanh vu khi"),
        ("shop", "Phim [ P ]", "Mo cua hang vu khi"),
        ("bag", "Phim [ I ]", "Mo balo ca nhan"),
        ("esc", "Phim [ ESC ]", "Tam dung / Quay sanh"),
    ]

    tip_font = get_font("Arial", 14, bold=True)
    val_font = get_font("Arial", 14, bold=False)
    KEY_COL = (210, 255, 100)
    TIP_COL = (170, 220, 170)

    row_y = 128
    for _, key_str, desc_str in guide_lines:
        row_rect = pygame.Rect(80, row_y, SCREEN_WIDTH - 160, 28)
        pygame.draw.rect(surface, (16, 26, 16), row_rect, border_radius=4)
        key_surf = tip_font.render(key_str, True, KEY_COL)
        desc_surf = val_font.render(desc_str, True, TIP_COL)
        surface.blit(key_surf, (row_rect.x + 12, row_rect.y + 6))
        surface.blit(desc_surf, (row_rect.x + 340, row_rect.y + 6))
        row_y += 34

    tip_box = pygame.Rect(80, row_y + 8, SCREEN_WIDTH - 160, 42)
    pygame.draw.rect(surface, (12, 35, 14), tip_box, border_radius=6)
    pygame.draw.rect(surface, (50, 160, 70), tip_box, 1, border_radius=6)
    tip_txt = val_font.render("?  Tranh xa dam may doc mau xanh - chung hut mau ban tung giay!", True, (100, 240, 120))
    surface.blit(tip_txt, (tip_box.x + 14, tip_box.y + 13))

    mouse_pos = pygame.mouse.get_pos()
    back_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 70, 220, 48)
    hover_back = back_rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, (90, 30, 30) if hover_back else (35, 15, 15), back_rect, border_radius=8)
    pygame.draw.rect(surface, (200, 60, 60) if hover_back else (100, 40, 40), back_rect, 1, border_radius=8)
    back_surf = font_btn.render("? QUAY LAI SANH", True, (220, 120, 120) if hover_back else (160, 80, 80))
    surface.blit(back_surf, (back_rect.x + (back_rect.width - back_surf.get_width()) // 2,
                             back_rect.y + (back_rect.height - back_surf.get_height()) // 2))

    return {"back": back_rect}

def draw_pause_menu(surface, font_title, font_btn):
    global is_dragging_bg, is_dragging_sfx, sound_volume, sfx_volume
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    surface.blit(overlay, (0, 0))
    
    panel_rect = pygame.Rect(180, 50, 440, 500)
    pygame.draw.rect(surface, (25, 28, 36), panel_rect, border_radius=8)
    pygame.draw.rect(surface, RED, panel_rect, 2, border_radius=8)
    
    title_surf = font_title.render("TAM DUNG", True, RED)
    surface.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 75))
    
    mouse_pos = pygame.mouse.get_pos()
    buttons = {}
    
    actions = [
        {"key": "resume", "text": "CHOI TIEP", "y": 150},
        {"key": "restart", "text": "CHOI LAI", "y": 210},
        {"key": "lobby", "text": "MENU CHINH", "y": 270}
    ]
    
    for act in actions:
        btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, act["y"], 260, 40)
        if btn_rect.collidepoint(mouse_pos):
            bg_col = (45, 110, 60) if act["key"] == "resume" else (50, 55, 65)
            border_col = YELLOW
        else:
            bg_col = (30, 50, 35) if act["key"] == "resume" else (35, 38, 46)
            border_col = GRAY
            
        pygame.draw.rect(surface, bg_col, btn_rect, border_radius=6)
        pygame.draw.rect(surface, border_col, btn_rect, 1, border_radius=6)
        
        txt_surf = font_btn.render(act["text"], True, WHITE)
        surface.blit(txt_surf, (btn_rect.x + (btn_rect.width // 2) - (txt_surf.get_width() // 2), 
                                btn_rect.y + (btn_rect.height // 2) - (txt_surf.get_height() // 2)))
        buttons[act["key"]] = btn_rect
        
    slider_x = 220
    slider_width = 360
    
    lbl_bg = font_btn.render(f"Am luong nhac nen: {int(sound_volume * 100)}%", True, WHITE)
    surface.blit(lbl_bg, (slider_x, 340))
    
    bg_track = pygame.Rect(slider_x, 365, slider_width, 8)
    pygame.draw.rect(surface, GRAY, bg_track, border_radius=4)
    
    fill_bg_w = int(slider_width * sound_volume)
    if fill_bg_w > 0:
        pygame.draw.rect(surface, GREEN, (slider_x, 365, fill_bg_w, 8), border_radius=4)
        
    handle_bg_x = slider_x + fill_bg_w
    pygame.draw.circle(surface, WHITE, (handle_bg_x, 369), 8)
    buttons["slider_bg_rect"] = bg_track
    
    lbl_sfx = font_btn.render(f"Am luong tieng sung (SFX): {int(sfx_volume * 100)}%", True, WHITE)
    surface.blit(lbl_sfx, (slider_x, 415))
    
    sfx_track = pygame.Rect(slider_x, 440, slider_width, 8)
    pygame.draw.rect(surface, GRAY, sfx_track, border_radius=4)
    
    fill_sfx_w = int(slider_width * sfx_volume)
    if fill_sfx_w > 0:
        pygame.draw.rect(surface, BLUE, (slider_x, 440, fill_sfx_w, 8), border_radius=4)
        
    handle_sfx_x = slider_x + fill_sfx_w
    pygame.draw.circle(surface, WHITE, (handle_sfx_x, 444), 8)
    buttons["slider_sfx_rect"] = sfx_track
    
    hint_txt = font_btn.render("Nhan [ ESC ] de quay lai tran dau nhanh", True, GRAY)
    surface.blit(hint_txt, (SCREEN_WIDTH // 2 - hint_txt.get_width() // 2, 505))
    
    return buttons

def draw_shop_menu(surface, font, player):
    global shop_buttons
    shop_buttons = []
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    shop_rect = pygame.Rect(100, 50, 600, 500)
    pygame.draw.rect(surface, (30, 35, 45), shop_rect)
    pygame.draw.rect(surface, BLUE, shop_rect, 3)
    
    title = font.render("CUA HANG SUNG", True, YELLOW)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70))
    
    mouse_pos = pygame.mouse.get_pos()
    
    shop_items = [
        {"id": 1, "text": f"Sung UMP - ${PRICES['UMP']}", "owned": player.inventory["UMP"], "icon": icon_ump, "color": WHITE},
        {"id": 2, "text": f"Sung AK-47 - ${PRICES['AK-47']}", "owned": player.inventory["AK-47"], "icon": icon_ak47, "color": WHITE},
        {"id": 3, "text": f"Sung Shotgun - ${PRICES['Shotgun']}", "owned": player.inventory["Shotgun"], "icon": icon_shotgun, "color": WHITE},
        {"id": 4, "text": f"Dan Sung UMP x30 - ${PRICES['Ammo_UMP']}", "owned": False, "icon": icon_ammo, "color": WHITE if player.inventory["UMP"] else GRAY},
        {"id": 5, "text": f"Dan Sung AK x30 - ${PRICES['Ammo_AK']}", "owned": False, "icon": icon_ammo, "color": WHITE if player.inventory["AK-47"] else GRAY},
        {"id": 6, "text": f"Dan Sung Shotgun x6 - ${PRICES['Ammo_Shotgun']}", "owned": False, "icon": icon_ammo, "color": WHITE if player.inventory["Shotgun"] else GRAY},
        {"id": 7, "text": f"Hop Cuu Thuong Medkit - ${PRICES['Medkit']}", "owned": False, "icon": icon_medkit, "color": WHITE}
    ]
    
    start_y = 130
    for item in shop_items:
        if item["owned"]:
            item["text"] = item["text"].split("-")[0] + "- DA SO HUU"
            item["color"] = GREEN
            
        if item["icon"]:
            icon_y = start_y + (font.get_height() // 2) - (item["icon"].get_height() // 2)
            surface.blit(item["icon"], (140, icon_y))
            
        text_surf = font.render(item["text"], True, item["color"])
        surface.blit(text_surf, (190, start_y))
        
        btn_rect = pygame.Rect(540, start_y - 2, 95, 24)
        if btn_rect.collidepoint(mouse_pos):
            btn_bg = (50, 200, 100) if item["id"] > 3 else (100, 100, 110)
            btn_border = WHITE
        else:
            btn_bg = (40, 140, 70) if item["id"] > 3 else (70, 75, 85)
            btn_border = GRAY
            
        if item["id"] <= 3 and "DA SO HUU" in item["text"]:
            btn_bg = (55, 60, 65)
            btn_border = (45, 50, 55)
            
        pygame.draw.rect(surface, btn_bg, btn_rect, border_radius=4)
        pygame.draw.rect(surface, btn_border, btn_rect, 1, border_radius=4)
        
        btn_label_str = "MUA" if (item["id"] > 3) else "SO HUU"
        btn_label = font.render(btn_label_str, True, WHITE)
        lbl_x = btn_rect.x + (btn_rect.width // 2) - (btn_label.get_width() // 2)
        lbl_y = btn_rect.y + (btn_rect.height // 2) - (btn_label.get_height() // 2)
        surface.blit(btn_label, (lbl_x, lbl_y))
        
        shop_buttons.append({"rect": btn_rect, "id": item["id"]})
        start_y += 38
        
    close_txt = font.render("Nhan [ P ] de DONG", True, WHITE)
    surface.blit(close_txt, (140, 495))

def draw_inventory_menu(surface, font, player):
    global inv_buttons
    inv_buttons = []
    
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    
    panel_rect = pygame.Rect(120, 60, 560, 480)
    pygame.draw.rect(surface, (40, 35, 45), panel_rect)
    pygame.draw.rect(surface, PURPLE, panel_rect, 3)
    
    title = font.render("BALO CA NHAN (INVENTORY)", True, YELLOW)
    surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 80))
    
    mouse_pos = pygame.mouse.get_pos()
    
    purchased_items = []
    if player.inventory["Pistol"]:
        purchased_items.append({"key": "Pistol", "name": "Sung Luc mac dinh", "info": "Dan: Vo han", "type": "weapon", "icon": icon_pistol})
    if player.inventory["UMP"]:
        purchased_items.append({"key": "UMP", "name": "Sung tieu lien UMP", "info": f"Hop dan du tru: {player.inventory['Ammo_UMP']}", "type": "weapon", "icon": icon_ump})
    if player.inventory["AK-47"]:
        purchased_items.append({"key": "AK-47", "name": "Sung truong AK-47", "info": f"Hop dan du tru: {player.inventory['Ammo_AK']}", "type": "weapon", "icon": icon_ak47})
    if player.inventory["Shotgun"]:
        purchased_items.append({"key": "Shotgun", "name": "Sung san Shotgun", "info": f"Hop dan du tru: {player.inventory['Ammo_Shotgun']}", "type": "weapon", "icon": icon_shotgun})
    if player.inventory["Medkit"] > 0:
        purchased_items.append({"key": "Medkit", "name": "Tui Cuu Thuong Medkit", "info": f"So luong: {player.inventory['Medkit']} cai", "type": "usable", "icon": icon_medkit})
        
    start_y = 140
    if not purchased_items:
        empty_lbl = font.render("Balo cua ban hien tai dang trong rong!", True, GRAY)
        surface.blit(empty_lbl, (SCREEN_WIDTH // 2 - empty_lbl.get_width() // 2, 220))
    else:
        for item in purchased_items:
            if item["icon"]:
                surface.blit(item["icon"], (150, start_y + 2))
            surface.blit(font.render(item["name"], True, WHITE), (210, start_y))
            surface.blit(font.render(item["info"], True, YELLOW), (380, start_y))
            
            action_rect = pygame.Rect(540, start_y - 2, 85, 24)
            if item["type"] == "weapon":
                is_equipped = (player.current_weapon == item["key"])
                btn_str = "TRANG BI" if is_equipped else "CHON DUNG"
                bg_color = (60, 60, 70) if is_equipped else (120, 50, 150)
                pygame.draw.rect(surface, bg_color, action_rect, border_radius=4)
                if action_rect.collidepoint(mouse_pos) and not is_equipped:
                    pygame.draw.rect(surface, WHITE, action_rect, 1, border_radius=4)
                lbl = font.render(btn_str, True, WHITE)
                surface.blit(lbl, (action_rect.x + (action_rect.width//2) - (lbl.get_width()//2), action_rect.y + (action_rect.height//2) - (lbl.get_height()//2)))
                inv_buttons.append({"rect": action_rect, "action": "equip", "value": item["key"]})
            elif item["type"] == "usable":
                pygame.draw.rect(surface, (40, 150, 80), action_rect, border_radius=4)
                if action_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(surface, WHITE, action_rect, 1, border_radius=4)
                lbl = font.render("SU DUNG", True, WHITE)
                surface.blit(lbl, (action_rect.x + (action_rect.width//2) - (lbl.get_width()//2), action_rect.y + (action_rect.height//2) - (lbl.get_height()//2)))
                inv_buttons.append({"rect": action_rect, "action": "use", "value": item["key"]})
            start_y += 38
            
    close_txt = font.render("Nhan [ I ] de DONG", True, WHITE)
    surface.blit(close_txt, (150, 490))

def handle_shop_purchase(item_id, player):
    if item_id == 1:
        if not player.inventory["UMP"] and player.gold >= PRICES["UMP"]:
            player.gold -= PRICES["UMP"]
            player.inventory["UMP"] = True
    elif item_id == 2:
        if not player.inventory["AK-47"] and player.gold >= PRICES["AK-47"]:
            player.gold -= PRICES["AK-47"]
            player.inventory["AK-47"] = True
    elif item_id == 3:
        if not player.inventory["Shotgun"] and player.gold >= PRICES["Shotgun"]:
            player.gold -= PRICES["Shotgun"]
            player.inventory["Shotgun"] = True
    elif item_id == 4:
        if player.inventory["UMP"] and player.gold >= PRICES["Ammo_UMP"]:
            player.gold -= PRICES["Ammo_UMP"]
            player.inventory["Ammo_UMP"] += 30
    elif item_id == 5:
        if player.inventory["AK-47"] and player.gold >= PRICES["Ammo_AK"]:
            player.gold -= PRICES["Ammo_AK"]
            player.inventory["Ammo_AK"] += 30
    elif item_id == 6:
        if player.inventory["Shotgun"] and player.gold >= PRICES["Ammo_Shotgun"]:
            player.gold -= PRICES["Ammo_Shotgun"]
            player.inventory["Ammo_Shotgun"] += 6
    elif item_id == 7:
        if player.gold >= PRICES["Medkit"]:
            player.gold -= PRICES["Medkit"]
            player.inventory["Medkit"] += 1

def handle_inventory_action(btn_click, player):
    if btn_click["action"] == "equip":
        player.current_weapon = btn_click["value"]
        player.animations = player.all_weapon_animations[player.current_weapon]
        player.frame_index = 0
        player.is_reloading = False
    elif btn_click["action"] == "use":
        if btn_click["value"] == "Medkit" and player.inventory["Medkit"] > 0:
            if player.hp < player.max_hp:
                player.hp = min(player.max_hp, player.hp + 40)
                player.inventory["Medkit"] -= 1

def show_level_up_screen(surface, font_title, font_btn, message):
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.fill((15, 22, 15))
    surface.blit(overlay, (0, 0))
    
    txt1 = font_title.render("VUOT QUA MAN CHOI THANH CONG!", True, GREEN)
    txt2 = font_btn.render(message, True, WHITE)
    txt3 = font_btn.render("Dang tai tai nguyen ban do moi...", True, YELLOW)
    
    surface.blit(txt1, (SCREEN_WIDTH // 2 - txt1.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
    surface.blit(txt2, (SCREEN_WIDTH // 2 - txt2.get_width() // 2, SCREEN_HEIGHT // 2))
    surface.blit(txt3, (SCREEN_WIDTH // 2 - txt3.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()
    pygame.time.delay(2200)

# ==========================================
# VÒNG LẶP CHÍNH (MAIN LOOP)
# ==========================================
def main():
    global sound_volume, sfx_volume, is_dragging_bg, is_dragging_sfx
    global story_current_page, story_displayed_lines, story_line_index
    global story_last_update, story_char_index, story_current_line, story_animation_active
    
    game_state = "LOBBY"
    current_level_id = 1
    
    # Biến lưu thông tin game over
    gameover_score = 0
    gameover_gold = 0
    gameover_level = ""
    
    level_start_ticks = 0
    paused_ticks_accumulator = 0
    pause_start_ticks = 0
    
    active_boss = None
    boss_spawned_this_level = False
    
    all_sprites = None
    zombies = None
    bullets = None
    coins = None
    buildings = None
    streetlights = None
    obstacles = None
    manholes = None
    toxic_zones = None
    effects_group = None
    player = None
    camera = None
    score = 0
    spawn_timer = 0
    is_shop_open = False
    is_bag_open = False
    
    def init_new_map_instance(keep_inventory_player=None):
        nonlocal all_sprites, zombies, bullets, coins, buildings, streetlights, obstacles, manholes, toxic_zones
        nonlocal player, camera, score, spawn_timer, is_shop_open, is_bag_open
        nonlocal level_start_ticks, paused_ticks_accumulator, active_boss, boss_spawned_this_level
        nonlocal effects_group
        
        all_sprites = pygame.sprite.Group()
        zombies = pygame.sprite.Group()
        bullets = pygame.sprite.Group()
        coins = pygame.sprite.Group()
        buildings = pygame.sprite.Group()
        streetlights = pygame.sprite.Group()
        obstacles = pygame.sprite.Group()
        manholes = pygame.sprite.Group()
        toxic_zones = pygame.sprite.Group()
        effects_group = pygame.sprite.Group()
        
        active_boss = None
        boss_spawned_this_level = False
        
        if keep_inventory_player:
            old_gold = keep_inventory_player.gold
            old_inv = keep_inventory_player.inventory
            old_weapons = keep_inventory_player.weapons
            old_cur_wpn = keep_inventory_player.current_weapon
            
            player = Player()
            player.gold = old_gold
            player.inventory = old_inv
            player.weapons = old_weapons
            player.current_weapon = old_cur_wpn
            player.animations = player.all_weapon_animations[old_cur_wpn]
        else:
            player = Player()
            
        all_sprites.add(player)
        camera = Camera(WORLD_WIDTH, WORLD_HEIGHT)
        
        building_images = []
        for i in ["building_1.png", "building_2.png", "building_3.png"]:
            if os.path.exists(i):
                try:
                    img = pygame.image.load(i).convert_alpha()
                    building_images.append(img)
                except pygame.error:
                    pass
                    
        random.seed(105 + current_level_id)
        
        # Tính danh sách các ô đất hợp lệ (block_col, block_row)
        land_blocks = []
        for bx_idx in range(0, WORLD_WIDTH, BLOCK_SIZE):
            for by_idx in range(0, WORLD_HEIGHT, BLOCK_SIZE):
                # Phần đất trong ô: từ (bx_idx+STREET_WIDTH) đến (bx_idx+BLOCK_SIZE)
                land_x_start = bx_idx + STREET_WIDTH
                land_y_start = by_idx + STREET_WIDTH
                land_w = BLOCK_SIZE - STREET_WIDTH
                land_h = BLOCK_SIZE - STREET_WIDTH
                if land_x_start + land_w <= WORLD_WIDTH and land_y_start + land_h <= WORLD_HEIGHT:
                    land_blocks.append((land_x_start, land_y_start, land_w, land_h))
        
        random.shuffle(land_blocks)
        
        p_safe_zone = pygame.Rect(WORLD_WIDTH // 2 - 300, WORLD_HEIGHT // 2 - 300, 700, 700)
        
        buildings_placed = 0
        for (lx, ly, lw, lh) in land_blocks:
            if buildings_placed >= 10:
                break
            # Kích thước tòa nhà: cố định lớn, gần bằng mảnh đất, padding 40px mỗi cạnh
            PADDING = 40
            bw_w = lw - PADDING * 2
            bw_h = lh - PADDING * 2
            if bw_w < 80 or bw_h < 80:
                continue
            # Đặt căn giữa trong ô đất
            bx = lx + PADDING
            by = ly + PADDING
            
            new_rect = pygame.Rect(bx, by, bw_w, bw_h)
            
            if new_rect.colliderect(p_safe_zone):
                continue
            if any(b.rect.colliderect(new_rect.inflate(40, 40)) for b in buildings):
                continue
                
            raw_img = random.choice(building_images) if building_images else None
            new_building = Building(bx, by, bw_w, bw_h, raw_img)
            buildings.add(new_building)
            obstacles.add(new_building)
            all_sprites.add(new_building)
            buildings_placed += 1
            
        for x in range(0, WORLD_WIDTH, BLOCK_SIZE):
            for y in range(0, WORLD_HEIGHT, BLOCK_SIZE):
                lx1 = x + STREET_WIDTH - 24
                ly1 = y + STREET_WIDTH + 60
                lx2 = x + BLOCK_SIZE // 2
                ly2 = y + STREET_WIDTH - 45
                
                test_rect1 = pygame.Rect(lx1, ly1, 24, 45)
                if not any(b.rect.colliderect(test_rect1.inflate(10, 10)) for b in buildings) and ly1 < WORLD_HEIGHT:
                    light1 = Streetlight(lx1, ly1)
                    streetlights.add(light1)
                    all_sprites.add(light1)
                    
                test_rect2 = pygame.Rect(lx2, ly2, 24, 45)
                if not any(b.rect.colliderect(test_rect2.inflate(10, 10)) for b in buildings) and lx2 < WORLD_WIDTH:
                    light2 = Streetlight(lx2, ly2)
                    streetlights.add(light2)
                    all_sprites.add(light2)
                    
                mx1 = x + STREET_WIDTH // 2
                my1 = y + STREET_WIDTH + random.randint(40, BLOCK_SIZE - 60)
                if my1 < WORLD_HEIGHT:
                    manholes.add(Manhole(mx1, my1))
                    
                mx2 = x + STREET_WIDTH + random.randint(40, BLOCK_SIZE - 60)
                my2 = y + STREET_WIDTH // 2
                if mx2 < WORLD_WIDTH:
                    manholes.add(Manhole(mx2, my2))
                    
        TOTAL_TOXIC_ZONES = 15
        for _ in range(TOTAL_TOXIC_ZONES):
            tx = random.randint(200, WORLD_WIDTH - 200)
            ty = random.randint(200, WORLD_HEIGHT - 200)
            if math.hypot(tx - player.rect.centerx, ty - player.rect.centery) > 300:
                zone = ToxicZone(tx, ty)
                toxic_zones.add(zone)
                
        score = 0
        spawn_timer = 0
        is_shop_open = False
        is_bag_open = False
        level_start_ticks = pygame.time.get_ticks()
        paused_ticks_accumulator = 0
        # Xây grid pathfinding cho zombie sau khi đã đặt xong buildings
        pf_build_grid(buildings)

    running = True
    while running:
        clock.tick(FPS)
        
        if game_state == "LOBBY":
            lobby_btns = draw_lobby_menu(screen, FONT_TITLE, FONT_BTN, current_level_id)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if "play_now" in lobby_btns and lobby_btns["play_now"].collidepoint(event.pos):
                        reset_story()
                        game_state = "STORY"
                    elif "level" in lobby_btns and lobby_btns["level"].collidepoint(event.pos):
                        game_state = "LEVEL_SELECT"
                    elif "guide" in lobby_btns and lobby_btns["guide"].collidepoint(event.pos):
                        game_state = "GUIDE"
                    elif "exit" in lobby_btns and lobby_btns["exit"].collidepoint(event.pos):
                        running = False
            continue
        
        elif game_state == "STORY":
            update_story_animation()
            draw_story_screen(screen)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                        result = handle_story_input()
                        if result == "EXIT_STORY":
                            init_new_map_instance()
                            game_state = "PLAYING"
            continue
            
        elif game_state == "LEVEL_SELECT":
            lvl_btns = draw_level_menu(screen, FONT_TITLE, FONT_BTN, current_level_id)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if lvl_btns["back"].collidepoint(event.pos):
                        game_state = "LOBBY"
                    elif lvl_btns["lvl_1"].collidepoint(event.pos):
                        current_level_id = 1
                        init_new_map_instance()
                        game_state = "PLAYING"
                    elif lvl_btns["lvl_2"].collidepoint(event.pos):
                        current_level_id = 2
                        init_new_map_instance()
                        game_state = "PLAYING"
                    elif lvl_btns["lvl_3"].collidepoint(event.pos):
                        current_level_id = 3
                        init_new_map_instance()
                        game_state = "PLAYING"
            continue
            
        elif game_state == "GUIDE":
            guide_btns = draw_guide_menu(screen, FONT_TITLE, FONT_GUIDE, FONT_BTN)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if "back" in guide_btns and guide_btns["back"].collidepoint(event.pos):
                        game_state = "LOBBY"
            continue
            
        elif game_state == "PAUSE":
            pause_btns = draw_pause_menu(screen, FONT_TITLE, FONT_BTN)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        paused_ticks_accumulator += (pygame.time.get_ticks() - pause_start_ticks)
                        game_state = "PLAYING"
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if pause_btns["resume"].collidepoint(event.pos):
                        paused_ticks_accumulator += (pygame.time.get_ticks() - pause_start_ticks)
                        game_state = "PLAYING"
                    elif pause_btns["restart"].collidepoint(event.pos):
                        init_new_map_instance()
                        game_state = "PLAYING"
                    elif pause_btns["lobby"].collidepoint(event.pos):
                        game_state = "LOBBY"
                    elif pause_btns["slider_bg_rect"].collidepoint(event.pos):
                        is_dragging_bg = True
                    elif pause_btns["slider_sfx_rect"].collidepoint(event.pos):
                        is_dragging_sfx = True
                        
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    is_dragging_bg = False
                    is_dragging_sfx = False
                    
                if event.type == pygame.MOUSEMOTION:
                    slider_x = 220
                    slider_width = 360
                    if is_dragging_bg:
                        relative_x = max(0, min(event.pos[0] - slider_x, slider_width))
                        sound_volume = relative_x / slider_width
                        pygame.mixer.music.set_volume(sound_volume)
                    if is_dragging_sfx:
                        relative_x = max(0, min(event.pos[0] - slider_x, slider_width))
                        sfx_volume = relative_x / slider_width
                        if sound_pistol: sound_pistol.set_volume(sfx_volume)
                        if sound_ak47: sound_ak47.set_volume(sfx_volume)
                        if sound_ump: sound_ump.set_volume(sfx_volume)
                        if sound_shotgun: sound_shotgun.set_volume(sfx_volume)
            continue

        elif game_state == "GAMEOVER":
            gameover_btns = draw_gameover_screen(screen, gameover_score, gameover_gold, gameover_level)
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if "retry" in gameover_btns and gameover_btns["retry"].collidepoint(event.pos):
                        # Giữ nguyên current_level_id, chơi lại đúng màn đang chơi
                        init_new_map_instance()
                        game_state = "PLAYING"
                    elif "quit" in gameover_btns and gameover_btns["quit"].collidepoint(event.pos):
                        # Quay về sảnh thay vì thoát game
                        game_state = "LOBBY"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        # Giữ nguyên current_level_id, chơi lại đúng màn đang chơi
                        init_new_map_instance()
                        game_state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        # Quay về sảnh thay vì thoát game
                        game_state = "LOBBY"
            continue

        # PLAYING STATE
        cfg_level = LEVELS[current_level_id]
        
        current_ticks = pygame.time.get_ticks()
        elapsed_seconds = (current_ticks - level_start_ticks - paused_ticks_accumulator) // 1000
        target_seconds = cfg_level["duration_minutes"] * 60
        remaining_seconds = max(0, target_seconds - elapsed_seconds)
        
        if current_level_id == 3 and remaining_seconds <= 0 and not boss_spawned_this_level:
            bx, by = None, None
            for _btry in range(50):
                _bx = player.rect.centerx + random.choice([-1, 1]) * random.randint(350, 500)
                _by = player.rect.centery + random.choice([-1, 1]) * random.randint(350, 500)
                _bx = max(200, min(_bx, WORLD_WIDTH - 200))
                _by = max(200, min(_by, WORLD_HEIGHT - 200))
                if is_on_street(_bx, _by, 60, 60):
                    _brect = pygame.Rect(_bx, _by, 60, 60)
                    if not any(b.rect.colliderect(_brect.inflate(80, 80)) for b in buildings):
                        bx, by = _bx, _by
                        break
            if bx is None:
                bx = (player.rect.centerx // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                by = (player.rect.centery // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                bx = max(200, min(bx + BLOCK_SIZE, WORLD_WIDTH - 200))
                by = max(200, min(by, WORLD_HEIGHT - 200))
            active_boss = BossZombie(bx, by)
            zombies.add(active_boss)
            all_sprites.add(active_boss)
            boss_spawned_this_level = True

        if current_level_id == 1 and remaining_seconds <= 0 and not boss_spawned_this_level:
            bx, by = None, None
            for _btry in range(50):
                _bx = player.rect.centerx + random.choice([-1, 1]) * random.randint(300, 450)
                _by = player.rect.centery + random.choice([-1, 1]) * random.randint(300, 450)
                _bx = max(200, min(_bx, WORLD_WIDTH - 200))
                _by = max(200, min(_by, WORLD_HEIGHT - 200))
                if is_on_street(_bx, _by, 60, 60):
                    _brect = pygame.Rect(_bx, _by, 60, 60)
                    if not any(b.rect.colliderect(_brect.inflate(80, 80)) for b in buildings):
                        bx, by = _bx, _by
                        break
            if bx is None:
                bx = (player.rect.centerx // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                by = (player.rect.centery // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                bx = max(200, min(bx + BLOCK_SIZE, WORLD_WIDTH - 200))
                by = max(200, min(by, WORLD_HEIGHT - 200))
            active_boss = BossZombieLv1(bx, by)
            zombies.add(active_boss)
            all_sprites.add(active_boss)
            boss_spawned_this_level = True

        if current_level_id == 2 and remaining_seconds <= 0 and not boss_spawned_this_level:
            bx, by = None, None
            for _btry in range(50):
                _bx = player.rect.centerx + random.choice([-1, 1]) * random.randint(350, 500)
                _by = player.rect.centery + random.choice([-1, 1]) * random.randint(350, 500)
                _bx = max(200, min(_bx, WORLD_WIDTH - 200))
                _by = max(200, min(_by, WORLD_HEIGHT - 200))
                if is_on_street(_bx, _by, 60, 60):
                    _brect = pygame.Rect(_bx, _by, 60, 60)
                    if not any(b.rect.colliderect(_brect.inflate(80, 80)) for b in buildings):
                        bx, by = _bx, _by
                        break
            if bx is None:
                bx = (player.rect.centerx // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                by = (player.rect.centery // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                bx = max(200, min(bx + BLOCK_SIZE, WORLD_WIDTH - 200))
                by = max(200, min(by, WORLD_HEIGHT - 200))
            active_boss = BossZombieLv2(bx, by)
            zombies.add(active_boss)
            all_sprites.add(active_boss)
            boss_spawned_this_level = True

        if remaining_seconds <= 0 and not boss_spawned_this_level:
            pass  # Chờ boss spawn (đã xử lý ở trên)
        
        # Khi hết giờ và boss đã spawn: KHÔNG tự chuyển màn, player phải giết boss
        # (Chỉ chuyển màn khi boss chết - xử lý trong phần bullet collision bên dưới)
        
        # Hiển thị nhắc nhở tiêu diệt boss khi boss đang sống
        if boss_spawned_this_level and active_boss and active_boss.alive() and remaining_seconds == 0:
            boss_warn_font = pygame.font.SysFont("Arial", 18, bold=True)
            if current_level_id == 1:
                bwarn = boss_warn_font.render("!! ALPHA BOSS XUAT HIEN - TIEU DIET DE TIEN TIEP !!", True, (255, 140, 0))
            elif current_level_id == 2:
                bwarn = boss_warn_font.render("!! BETA BOSS XUAT HIEN - TIEU DIET DE TIEN TIEP !!", True, (60, 160, 255))
            else:
                bwarn = boss_warn_font.render("!! TYRANT BOSS XUAT HIEN - TIEU DIET DE CHIEN THANG !!", True, (255, 0, 200))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pause_start_ticks = pygame.time.get_ticks() 
                    game_state = "PAUSE"
                    continue
                if event.key == pygame.K_p:
                    if not is_bag_open:
                        is_shop_open = not is_shop_open
                if event.key == pygame.K_i:
                    if not is_shop_open:
                        is_bag_open = not is_bag_open
                if event.key == pygame.K_r:
                    if not is_shop_open and not is_bag_open:
                        player.start_reload_sequence()
                if event.key == pygame.K_q:
                    if not is_shop_open and not is_bag_open:
                        player.switch_weapon_quick()
                if event.key == pygame.K_1:
                    if not is_shop_open and not is_bag_open:
                        player.current_weapon = "Pistol"
                        player.animations = player.all_weapon_animations["Pistol"]
                        player.frame_index = 0
                if event.key == pygame.K_2 and player.inventory["UMP"]:
                    if not is_shop_open and not is_bag_open:
                        player.current_weapon = "UMP"
                        player.animations = player.all_weapon_animations["UMP"]
                        player.frame_index = 0
                if event.key == pygame.K_3 and player.inventory["AK-47"]:
                    if not is_shop_open and not is_bag_open:
                        player.current_weapon = "AK-47"
                        player.animations = player.all_weapon_animations["AK-47"]
                        player.frame_index = 0
                if event.key == pygame.K_4 and player.inventory["Shotgun"]:
                    if not is_shop_open and not is_bag_open:
                        player.current_weapon = "Shotgun"
                        player.animations = player.all_weapon_animations["Shotgun"]
                        player.frame_index = 0
                        
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if is_shop_open:
                    for btn in shop_buttons:
                        if btn["rect"].collidepoint(event.pos):
                            handle_shop_purchase(btn["id"], player)
                elif is_bag_open:
                    for btn in inv_buttons:
                        if btn["rect"].collidepoint(event.pos):
                            handle_inventory_action(btn, player)

        if not is_shop_open and not is_bag_open:
            mouse_buttons = pygame.mouse.get_pressed()
            if mouse_buttons[0]:
                new_bullets = player.shoot(camera)
                if new_bullets:
                    if sfx_volume > 0:
                        if player.current_weapon == "Pistol" and sound_pistol: sound_pistol.play()
                        elif player.current_weapon == "UMP" and sound_ump: sound_ump.play()
                        elif player.current_weapon == "AK-47" and sound_ak47: sound_ak47.play()
                        elif player.current_weapon == "Shotgun" and sound_shotgun: sound_shotgun.play()
                    for bullet in new_bullets:
                        all_sprites.add(bullet)
                        bullets.add(bullet)
                        
            spawn_timer += 1
            if spawn_timer >= cfg_level["spawn_rate"]:
                # Thử tìm vị trí hợp lệ cho zombie: PHẢI trên đường, không trong/sát nhà, đủ xa player
                ZOMBIE_W, ZOMBIE_H = 65, 65
                SAFE_MARGIN = 60  # khoảng cách tối thiểu với nhà
                BORDER_MARGIN = STREET_WIDTH + 10  # tránh spawn sát biên map
                valid_spawn = False
                zx, zy = -9999, -9999
                for _spawn_try in range(40):
                    zx = random.randint(BORDER_MARGIN, WORLD_WIDTH - BORDER_MARGIN)
                    zy = random.randint(BORDER_MARGIN, WORLD_HEIGHT - BORDER_MARGIN)
                    # Bắt buộc spawn trên đường (không trong ô đất/nhà)
                    if not is_on_street(zx, zy, ZOMBIE_W, ZOMBIE_H):
                        continue
                    temp_rect = pygame.Rect(zx, zy, ZOMBIE_W, ZOMBIE_H)
                    # Kiểm tra khoảng cách an toàn với nhà
                    collide_building = any(b.rect.colliderect(temp_rect.inflate(SAFE_MARGIN * 2, SAFE_MARGIN * 2)) for b in buildings)
                    if collide_building:
                        continue
                    dist_p = math.hypot(zx - player.rect.centerx, zy - player.rect.centery)
                    if dist_p > 300:
                        valid_spawn = True
                        break

                if valid_spawn and len(zombies) < 45:
                    spd = random.uniform(cfg_level["zombie_speed_min"], cfg_level["zombie_speed_max"])
                    new_zombie = Zombie(zx, zy, spd)
                    zombies.add(new_zombie)
                    all_sprites.add(new_zombie)
                spawn_timer = 0
                
            player.update(obstacles)
            zombies.update(player.rect, obstacles)
            bullets.update()
            toxic_zones.update()
            effects_group.update()
            
            for bullet in bullets:
                hit_obstacles = pygame.sprite.spritecollide(bullet, obstacles, False)
                if hit_obstacles:
                    bullet.kill()
                    continue
                hit_zombies = pygame.sprite.spritecollide(bullet, zombies, False)
                for zombie in hit_zombies:
                    bullet.kill()
                    zombie.hp -= bullet.damage
                    if zombie.hp <= 0:
                        is_boss_kill = (zombie == active_boss)
                        # Zombie nổ: khi chết kích nổ
                        if isinstance(zombie, ZombieExploder):
                            ex = ExplosionEffect(zombie.rect.centerx, zombie.rect.centery, zombie.explode_radius)
                            all_sprites.add(ex)
                            effects_group.add(ex)
                            # Damage player nếu trong vùng nổ
                            dist_p = math.hypot(player.rect.centerx - zombie.rect.centerx,
                                                player.rect.centery - zombie.rect.centery)
                            if dist_p < zombie.explode_radius:
                                player.hp -= zombie.explode_damage * (1 - dist_p / zombie.explode_radius)
                        if is_boss_kill:
                            active_boss = None
                        zombie.kill()
                        score += 1
                        # Spawn coin rơi từ zombie (luôn rơi, không cộng vàng trực tiếp)
                        coin_value = zombie.gold_reward
                        coin = Coin(zombie.rect.centerx, zombie.rect.centery, coin_value)
                        coins.add(coin)
                        all_sprites.add(coin)
                        # 35% cơ hội rơi thêm coin bonus
                        if random.random() < 0.35:
                            bonus_coin = Coin(zombie.rect.centerx + random.randint(-20, 20),
                                             zombie.rect.centery + random.randint(-20, 20), 10)
                            coins.add(bonus_coin)
                            all_sprites.add(bonus_coin)
                        # ── THẮNG KHI BOSS CHẾT ──
                        if is_boss_kill and current_level_id == 3:
                            is_shop_open = False
                            is_bag_open  = False
                            show_level_up_screen(screen, FONT_TITLE, FONT_BTN,
                                "TYRANT BOSS DA BI TIEU DIET! CHUC MUNG CHIEN THANG!")
                            game_state = "LOBBY"
                            current_level_id = 1
                            break
                        elif is_boss_kill and current_level_id == 1:
                            is_shop_open = False
                            is_bag_open  = False
                            show_level_up_screen(screen, FONT_TITLE, FONT_BTN,
                                "ALPHA BOSS DA BI TIEU DIET! TIEN VAO MAN 2!")
                            current_level_id = 2
                            init_new_map_instance(keep_inventory_player=player)
                            break
                        elif is_boss_kill and current_level_id == 2:
                            is_shop_open = False
                            is_bag_open  = False
                            show_level_up_screen(screen, FONT_TITLE, FONT_BTN,
                                "BETA BOSS DA BI TIEU DIET! TIEN VAO MAN CUOI CUNG!")
                            current_level_id = 3
                            init_new_map_instance(keep_inventory_player=player)
                            break
                else:
                    continue
                break  # thoát vòng for bullet nếu đã xử lý boss kill → vào lại loop chính

            # ── XỬ LÝ SKILL BOSS: GROUNDSLAM ─────────────────
            if active_boss and active_boss.alive() and active_boss.pending_explosions:
                for (ex, ey) in active_boss.pending_explosions:
                    eff = ExplosionEffect(ex, ey, active_boss.slam_radius)
                    all_sprites.add(eff)
                    effects_group.add(eff)
                    # Gây sát thương cho player
                    dist_p = math.hypot(player.rect.centerx - ex, player.rect.centery - ey)
                    if dist_p < active_boss.slam_radius:
                        ratio = 1.0 - dist_p / active_boss.slam_radius
                        player.hp -= active_boss.slam_damage * ratio
                active_boss.pending_explosions.clear()

            # ── XỬ LÝ SKILL BOSS: SUMMON ──────────────────────
            if active_boss and active_boss.alive() and active_boss.pending_summons:
                for (sx, sy, ztype) in active_boss.pending_summons:
                    if len(zombies) >= 55:
                        break
                    # Tìm vị trí hợp lệ trên đường gần sx, sy
                    valid_sx, valid_sy = None, None
                    for _stry in range(20):
                        _sx = sx + random.randint(-100, 100)
                        _sy = sy + random.randint(-100, 100)
                        _sx = max(100, min(_sx, WORLD_WIDTH - 100))
                        _sy = max(100, min(_sy, WORLD_HEIGHT - 100))
                        if is_on_street(_sx, _sy, 50, 50):
                            _srect = pygame.Rect(_sx, _sy, 50, 50)
                            if not any(b.rect.colliderect(_srect.inflate(60, 60)) for b in buildings):
                                valid_sx, valid_sy = _sx, _sy
                                break
                    if valid_sx is None:
                        # Fallback: snap về giao lộ gần nhất
                        valid_sx = (sx // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                        valid_sy = (sy // BLOCK_SIZE) * BLOCK_SIZE + STREET_WIDTH // 2
                        valid_sx = max(100, min(valid_sx, WORLD_WIDTH - 100))
                        valid_sy = max(100, min(valid_sy, WORLD_HEIGHT - 100))
                    if ztype == "exploder":
                        nz = ZombieExploder(valid_sx, valid_sy)
                    elif ztype == "tank":
                        nz = ZombieTank(valid_sx, valid_sy)
                    else:
                        nz = ZombieSpeeder(valid_sx, valid_sy)
                    zombies.add(nz)
                    all_sprites.add(nz)
                active_boss.pending_summons.clear()
                            
            collected_coins = pygame.sprite.spritecollide(player, coins, True)
            for c in collected_coins:
                player.gold += c.value

            # Cập nhật hút xu (magnet) + BFS tìm xu gần nhất
            for c in coins:
                c.update(player.rect)
            # BFS player: tìm xu gần nhất (cập nhật mỗi 15 frame)
            if not hasattr(player, '_bfs_coin_timer'):
                player._bfs_coin_timer = 0
                player._bfs_nearest_coin = None
            player._bfs_coin_timer += 1
            if player._bfs_coin_timer >= 15:
                player._bfs_coin_timer = 0
                player._bfs_nearest_coin = bfs_find_nearest_coin(
                    player.pos_x, player.pos_y, coins)
            # Nếu xu đã bị nhặt thì bỏ reference
            if player._bfs_nearest_coin and not player._bfs_nearest_coin.alive():
                player._bfs_nearest_coin = None
                
            for zone in toxic_zones:
                if zone.check_player_collision(player.rect):
                    player.hp -= cfg_level["toxic_damage"]
                    
            zombies_attacking = pygame.sprite.spritecollide(player, zombies, False)
            if zombies_attacking:
                for z in zombies_attacking:
                    if isinstance(z, BossZombie):
                        player.hp -= 2.5
                    elif isinstance(z, BossZombieLv2):
                        player.hp -= 1.8
                    elif isinstance(z, BossZombieLv1):
                        player.hp -= 1.2
                    elif isinstance(z, ZombieTank):
                        damage_multiplier = 1.0 if current_level_id == 1 else (1.5 if current_level_id == 2 else 2.5)
                        player.hp -= 0.6 * damage_multiplier * z.damage_mult
                    else:
                        damage_multiplier = 1.0 if current_level_id == 1 else (1.5 if current_level_id == 2 else 2.5)
                        player.hp -= 0.6 * damage_multiplier
                
            if player.hp <= 0:
                gameover_score = score
                gameover_gold = player.gold
                gameover_level = cfg_level["name"]
                game_state = "GAMEOVER"

        screen.fill(BG_WORLD)              
        camera.draw_world_blocks(screen)   
        camera.draw_streets(screen)        

        for m in manholes:
            screen.blit(m.image, camera.apply(m))

        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))

        # ── VẼ TIA XANH BFS: Người chơi → Xu gần nhất ──────────────────────────
        if (hasattr(player, '_bfs_nearest_coin') and 
                player._bfs_nearest_coin and 
                player._bfs_nearest_coin.alive() and
                coins):
            nc = player._bfs_nearest_coin
            # Tọa độ màn hình
            px_s = player.rect.centerx - camera.x
            py_s = player.rect.centery - camera.y
            cx_s = nc.rect.centerx - camera.x
            cy_s = nc.rect.centery - camera.y
            t = pygame.time.get_ticks()
            # Tia nhấp nháy nhẹ theo thời gian
            alpha_pulse = int(160 + 80 * math.sin(t * 0.008))
            dist_line = math.hypot(cx_s - px_s, cy_s - py_s)
            if dist_line > 0:
                # Vẽ nhiều đoạn ngắn với alpha
                segments = max(4, int(dist_line // 12))
                line_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                for i in range(segments):
                    t0 = i / segments
                    t1 = (i + 1) / segments
                    sx0 = int(px_s + (cx_s - px_s) * t0)
                    sy0 = int(py_s + (cy_s - py_s) * t0)
                    sx1 = int(px_s + (cx_s - px_s) * t1)
                    sy1 = int(py_s + (cy_s - py_s) * t1)
                    seg_alpha = int(alpha_pulse * (0.3 + 0.7 * (1 - t0)))  # nhạt dần về phía xu
                    col = (30, 220, 120, seg_alpha)
                    pygame.draw.line(line_surf, col, (sx0, sy0), (sx1, sy1), 2)
                screen.blit(line_surf, (0, 0))
                # Vòng tròn nhỏ nhấp nháy ở xu mục tiêu
                ring_r = int(10 + 4 * math.sin(t * 0.01))
                ring_surf = pygame.Surface((ring_r*2+4, ring_r*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (50, 255, 150, 100), (ring_r+2, ring_r+2), ring_r, 2)
                screen.blit(ring_surf, (cx_s - ring_r - 2, cy_s - ring_r - 2))

        # Vẽ hiệu ứng nổ (lớp trên cùng)
        for eff in effects_group:
            screen.blit(eff.image, camera.apply(eff))

        for zone in toxic_zones:
            screen.blit(zone.image, camera.apply(zone))

        for zombie in zombies:
            if not isinstance(zombie, (BossZombie, BossZombieLv1, BossZombieLv2)):
                zombie.draw_hp_bar(screen, camera)

        # Cảnh báo SLAM của boss
        if active_boss and active_boss.alive() and active_boss.is_slamming:
            warn_font = pygame.font.SysFont("Arial", 22, bold=True)
            t = active_boss.slam_anim_timer / active_boss.slam_anim_frames
            alpha = int(200 * abs(math.sin(t * math.pi * 3)))
            warn_surf = warn_font.render("!! GROUNDSLAM !!", True, (255, 80, 0))
            warn_surf.set_alpha(alpha)
            screen.blit(warn_surf, (SCREEN_WIDTH // 2 - warn_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        # Cảnh báo SUMMON của boss
        if active_boss and active_boss.alive() and active_boss.is_summoning:
            warn_font = pygame.font.SysFont("Arial", 22, bold=True)
            t = active_boss.summon_anim_timer / active_boss.summon_anim_frames
            alpha = int(200 * abs(math.sin(t * math.pi * 3)))
            warn_surf = warn_font.render("!! SUMMONING UNDEAD !!", True, (160, 0, 255))
            warn_surf.set_alpha(alpha)
            screen.blit(warn_surf, (SCREEN_WIDTH // 2 - warn_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

        player.draw_reload_text(screen, camera, FONT_HUD)
        player.draw_hud(screen, FONT_HUD, score, cfg_level["name"], remaining_seconds)
        
        # Vẽ cảnh báo boss đang hoạt động
        if boss_spawned_this_level and active_boss and active_boss.alive():
            boss_warn_font2 = pygame.font.SysFont("Arial", 16, bold=True)
            if current_level_id == 1:
                bwarn2 = boss_warn_font2.render(">> TIEU DIET ALPHA BOSS DE VUOT MAN! <<", True, (255, 140, 0))
            elif current_level_id == 2:
                bwarn2 = boss_warn_font2.render(">> TIEU DIET BETA BOSS DE VUOT MAN! <<", True, (60, 200, 255))
            else:
                bwarn2 = boss_warn_font2.render(">> TIEU DIET TYRANT BOSS DE CHIEN THANG! <<", True, (255, 80, 255))
            pulse_alpha = int(180 + 70 * abs(math.sin(pygame.time.get_ticks() * 0.004)))
            bwarn2.set_alpha(pulse_alpha)
            screen.blit(bwarn2, (SCREEN_WIDTH // 2 - bwarn2.get_width() // 2, SCREEN_HEIGHT - 38))
        
        if active_boss and active_boss.alive():
            active_boss.draw_boss_bar(screen)
            active_boss.draw_algo_label(screen, camera)
            
        camera.update(player)
        camera.draw_minimap(screen, player, zombies, coins, buildings)
        
        if is_shop_open:
            draw_shop_menu(screen, FONT_HUD, player)
        elif is_bag_open:
            draw_inventory_menu(screen, FONT_HUD, player)
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()