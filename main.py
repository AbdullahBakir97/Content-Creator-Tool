import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
from io import BytesIO
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
import sys
import re
# إعدادات FFmpeg
root = tk.Tk()
root.title("أداة عمل المحتوى من قناة مدرسة الذكاء الاصطناعي")
root.geometry("930x820")
root.resizable(False, False)

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS  # عند تشغيل ملف EXE
    ffmpeg_exe = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')
else:
    base_path = os.path.dirname(os.path.abspath(__file__))  # عند تشغيل PyCharm
    ffmpeg_exe = os.path.join(base_path, 'ffmpeg', 'ffmpeg.exe')


background_image_path = os.path.join(base_path, "background.png")
background_image = Image.open(background_image_path)
background_photo = ImageTk.PhotoImage(background_image)

canvas = tk.Canvas(root, width=930, height=820)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=background_photo, anchor="nw")

# إعدادات الأيقونات
icons = {
    "YouTube": ("icons/youtube_icon.png", "icons/youtube_icon_hover.png", "https://youtube.com/@arabianAiSchool/"),
    "Instagram": ("icons/instagram_icon.png", "icons/instagram_icon_hover.png", "https://www.instagram.com/arabianaischool"),
    "Twitter": ("icons/twitter_icon.png", "icons/twitter_icon_hover.png", "https://twitter.com/arabianaischool"),
    "Facebook": ("icons/facebook_icon.png", "icons/facebook_icon_hover.png", "https://www.facebook.com/arabianaischool")
}

icon_positions = [(300, 170), (370, 170), (440, 170), (510, 170)]
icon_labels = []

def on_enter_icon(event, icon_label, hover_photo):
    icon_label.config(image=hover_photo)

def on_leave_icon(event, icon_label, photo):
    icon_label.config(image=photo)

def open_link(url):
    import webbrowser
    webbrowser.open(url)

for (name, (icon_path, hover_icon_path, url)), (x, y) in zip(icons.items(), icon_positions):
    icon_image = Image.open(os.path.join(base_path, icon_path))
    icon_hover_image = Image.open(os.path.join(base_path, hover_icon_path))

    icon_image = icon_image.resize((50, 50), Image.LANCZOS)
    icon_hover_image = icon_hover_image.resize((50, 50), Image.LANCZOS)

    icon_photo = ImageTk.PhotoImage(icon_image)
    icon_hover_photo = ImageTk.PhotoImage(icon_hover_image)

    icon_label = tk.Label(root, image=icon_photo, cursor="hand2", bg="#000000")
    icon_label.image = icon_photo
    icon_label.place(x=x, y=y)
    icon_label.bind("<Button-1>", lambda e, url=url: open_link(url))
    icon_label.bind("<Enter>", lambda e, icon_label=icon_label, hover_photo=icon_hover_photo: on_enter_icon(e, icon_label, hover_photo))
    icon_label.bind("<Leave>", lambda e, icon_label=icon_label, photo=icon_photo: on_leave_icon(e, icon_label, photo))
    icon_labels.append(icon_label)

# الحقول المدخلة
gemini_label = tk.Label(root, text="أدخل مفتاح جيميناي:", font=("Arial", 14, "bold"), bg="#000000", fg="#FFFFFF")
gemini_label.place(x=660, y=240)
gemini_entry = ttk.Entry(root, width=40, font=("Arial", 14))
gemini_entry.place(x=200, y=240)

eleven_label = tk.Label(root, text="أدخل مفتاح الفن لابس", font=("Arial", 14, "bold"), bg="#000000", fg="#FFFFFF")
eleven_label.place(x=660, y=280)
eleven_entry = ttk.Entry(root, width=40, font=("Arial", 14))
eleven_entry.place(x=200, y=280)

# تمكين النسخ واللصق في حقول الإدخال
def paste_into_entry(event, entry):
    try:
        entry.insert(tk.INSERT, root.clipboard_get())
    except tk.TclError:
        pass

def create_entry_context_menu(entry):
    menu = tk.Menu(entry, tearoff=0)
    menu.add_command(label="قص", command=lambda: entry.event_generate('<<Cut>>'))
    menu.add_command(label="نسخ", command=lambda: entry.event_generate('<<Copy>>'))
    menu.add_command(label="لصق", command=lambda: entry.event_generate('<<Paste>>'))

    def show_context_menu(event):
        menu.tk_popup(event.x_root, event.y_root)
        return "break"

    entry.bind("<Button-3>", show_context_menu)  # للويندوز
    entry.bind("<Button-2>", show_context_menu)  # للماك

# ربط Ctrl+V بحقول الإدخال
gemini_entry.bind('<Control-v>', lambda event: paste_into_entry(event, gemini_entry))
eleven_entry.bind('<Control-v>', lambda event: paste_into_entry(event, eleven_entry))

# إنشاء قوائم منبثقة لحقول الإدخال
create_entry_context_menu(gemini_entry)
create_entry_context_menu(eleven_entry)

# قائمة نوع المحتوى مع الأنواع الجديدة
content_types = ["رياضي", "ترفيهي", "اخباري", "معلومات عامة", "تحفيزي"]
content_type_label = tk.Label(root, text="اختر نوع المحتوى", font=("Arial", 14, "bold"), bg="#000000", fg="#FFFFFF")
content_type_label.place(x=660, y=330)
content_type_combo = ttk.Combobox(root, values=content_types, font=("Arial", 14))
content_type_combo.place(x=400, y=330)
content_type_combo.current(0)

# قسم الجدولة
schedule_label = tk.Label(root, text="حدد وقت عمل الفيديو", font=("Arial", 14, "bold"), bg="#000000", fg="#FFFFFF")
schedule_label.place(x=660, y=380)
hour_label = tk.Label(root, text="ساعة", font=("Arial", 12, "bold"), bg="#000000", fg="#FFFFFF")
hour_label.place(x=600, y=380)
minute_label = tk.Label(root, text="دقيقة:", font=("Arial", 12, "bold"), bg="#000000", fg="#FFFFFF")
minute_label.place(x=400, y=380)
hour_entry = ttk.Combobox(root, values=[f"{i:02}" for i in range(24)], width=5, font=("Arial", 12))
hour_entry.place(x=490, y=380)
minute_entry = ttk.Combobox(root, values=[f"{i:02}" for i in range(60)], width=5, font=("Arial", 12))
minute_entry.place(x=280, y=380)

# تأثيرات الأزرار عند المرور عليها
def on_enter_save_button(event):
    save_button.config(image=save_button_hover_photo)

def on_leave_save_button(event):
    save_button.config(image=save_button_photo)

save_button_image_path = os.path.join(base_path, "save_button.png")
save_button_hover_image_path = os.path.join(base_path, "save_button_hover.png")
save_button_image = Image.open(save_button_image_path).resize((300, 70), Image.LANCZOS)
save_button_hover_image = Image.open(save_button_hover_image_path).resize((300, 70), Image.LANCZOS)
save_button_photo = ImageTk.PhotoImage(save_button_image)
save_button_hover_photo = ImageTk.PhotoImage(save_button_hover_image)

save_button = tk.Button(root, image=save_button_photo, command=lambda: print("Settings Saved"), borderwidth=0, bg="#000000")
save_button.place(x=340, y=450)
save_button.bind("<Enter>", on_enter_save_button)
save_button.bind("<Leave>", on_leave_save_button)

def on_enter_export_button(event):
    export_button.config(image=export_button_hover_photo)

def on_leave_export_button(event):
    export_button.config(image=export_button_photo)

export_button_image_path = os.path.join(base_path, "export_button.png")
export_button_hover_image_path = os.path.join(base_path, "export_button_hover.png")
export_button_image = Image.open(export_button_image_path).resize((300, 70), Image.LANCZOS)
export_button_hover_image = Image.open(export_button_hover_image_path).resize((300, 70), Image.LANCZOS)
export_button_photo = ImageTk.PhotoImage(export_button_image)
export_button_hover_photo = ImageTk.PhotoImage(export_button_hover_image)

export_button = tk.Button(root, image=export_button_photo, command=lambda: create_content(), borderwidth=0, bg="#000000")
export_button.place(x=340, y=570)
export_button.bind("<Enter>", on_enter_export_button)
export_button.bind("<Leave>", on_leave_export_button)

# وظيفة إنشاء النص بناءً على نوع المحتوى
def generate_script_based_on_content_type(api_key, content_type):
    genai.configure(api_key=api_key)
    if content_type == "رياضي":
        prompt = "ااكتب نصًا باللغة العربية لفيديو مدته 60 ثانية لقناة يوتيوب متخصصة في حقائق كرة القدم. يجب أن يكون النص جذابًا ومثيرًا، يركز على قصة أو حقيقة عن لاعب كرة قدم أو مدرب أو حدث مهم في عالم كرة القدم. امزج بين الإثارة والواقعية. اذكر كيف غير هذا الشخص أو الحدث مسار مباراة أو بطولة مهمة بطريقة غير متوقعة. قم بتضمين دعوة للمشاهدين للإعجاب بالفيديو والتعليق والاشتراك في القناة لمزيد من الفيديوهات. اجعل الأسلوب حيويًا وشيقًا، مع التركيز على جذب الانتباه بسرعة. لا تذكر توجيهات مشهدية أو إشارات بصرية محددة في النص"
    elif content_type == "ترفيهي":
        prompt = "اكتب نصًا باللغة العربية لفيديو مدته 60 ثانية لقناة يوتيوب ترفيهية..."
    elif content_type == "اخباري":
        prompt = "اكتب نصًا باللغة العربية لفيديو مدته 60 ثانية لقناة يوتيوب إخبارية. يجب أن يكون النص دقيقًا ومثيرًا، يركز على خبر حديث أو حدث مهم يجري الآن في العالم أو المنطقة. امزج بين المعلومات والموضوعية. اذكر التفاصيل الأساسية وكيف يؤثر هذا الخبر على الجمهور أو المجتمع بشكل عام. قم بتضمين دعوة للمشاهدين للإعجاب بالفيديو والتعليق والاشتراك في القناة لمزيد من التحديثات الإخبارية. اجعل الأسلوب واضحًا وجذابًا، مع التركيز على نقل المعلومة بسرعة وفعالية. لا تذكر توجيهات مشهدية أو إشارات بصرية محددة في النص."
    elif content_type == "معلومات عامة":
        prompt = "اكتب نصًا باللغة العربية لفيديو مدته 60 ثانية لقناة يوتيوب تقدم معلومات عامة مفيدة. يجب أن يكون النص مفيدًا ومثيرًا للاهتمام، يركز على معلومة أو حقيقة غير معروفة عن موضوع مثل العلوم، التاريخ، الثقافة، أو الطبيعة. امزج بين المعرفة والتشويق. اذكر كيف يمكن لهذه المعلومة أن توسع آفاق المشاهدين أو تغير فهمهم لموضوع معين. قم بتضمين دعوة للمشاهدين للإعجاب بالفيديو والتعليق والاشتراك في القناة لمزيد من المحتوى المثير للاهتمام. اجعل الأسلوب حيويًا وجاذبًا، مع التركيز على تقديم المعلومة بطريقة سهلة الفهم. لا تذكر توجيهات مشهدية أو إشارات بصرية محددة في النص"
    elif content_type == "تحفيزي":
        prompt = "اكتب نصًا باللغة العربية لفيديو مدته 60 ثانية لقناة يوتيوب تحفيزية. يجب أن يكون النص ملهمًا ومحفزًا، يركز على قصة نجاح، اقتباس مؤثر، أو رسالة تشجيعية تدفع المشاهدين لتحقيق أهدافهم. امزج بين الإلهام والواقعية. اذكر كيف يمكن للتفاني والإصرار أن يغير حياة الشخص بشكل إيجابي. قم بتضمين دعوة للمشاهدين للإعجاب بالفيديو والتعليق والاشتراك في القناة لمزيد من المحتوى التحفيزي. اجعل الأسلوب مؤثرًا وجاذبًا، مع التركيز على تحفيز المشاهدين لاتخاذ خطوات إيجابية. لا تذكر توجيهات مشهدية أو إشارات بصرية محددة في النص"

    else:
        prompt = ""

    if not prompt:
        return ""

    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])
    response = chat.send_message(prompt)
    return response.text

# تنظيف النص
def clean_script(script):
    lines = script.split('\n')
    cleaned_lines = [line for line in lines if not any(word in line.lower() for word in ['مشهد', 'صورة', 'لقطة'])]
    return '\n'.join(cleaned_lines)

# إنشاء التعليق الصوتي باستخدام Eleven Labs API
def generate_voiceover(script, api_key):
    try:
        url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        data = {
            "text": script,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        output_audio_filename = 'arabic_voiceover.mp3'
        with open(output_audio_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print(f"تم إنشاء الصوت وحفظه كـ {output_audio_filename}")
        return output_audio_filename
    except Exception as e:
        print(f"Error generating voiceover: {e}")
        return None

# استخراج المصطلحات الأساسية للصور
def extract_arabic_key_terms(script):
    words = re.findall(r'\b\w+\b', script)
    return list(set(words))

# تنزيل صور عالية الجودة من Bing وتعديل حجمها
def download_images_from_bing(query, num_images, folder):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://www.bing.com/images/search?q={query}&FORM=HDRSC2"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    image_elements = soup.find_all('a', {'class': 'iusc'})

    os.makedirs(folder, exist_ok=True)
    image_count = 0

    for i, img_element in enumerate(image_elements):
        if image_count >= num_images:
            break
        m = img_element.get('m')
        if m:
            m = json.loads(m)
            img_url = m['murl']

            if img_url:
                try:
                    img_data = requests.get(img_url, headers=headers, timeout=10).content
                    img = Image.open(BytesIO(img_data))
                    img = resize_and_crop_image(img)
                    img_filename = os.path.join(folder, f'image_{image_count + 1}.jpg')
                    img.save(img_filename, format='JPEG', quality=95)
                    image_count += 1
                    print(f"Downloaded {img_filename}")
                except Exception as e:
                    print(f"Failed to download image {i + 1}: {e}")

# تعديل حجم الصورة إلى 1080x1920
def resize_and_crop_image(img):
    target_size = (1080, 1920)
    img_ratio = img.width / img.height
    target_ratio = target_size[0] / target_size[1]

    if img_ratio > target_ratio:
        # قص العرض
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # قص الارتفاع
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    img = img.resize(target_size, Image.LANCZOS)
    return img

# إنشاء الفيديو مع الترجمة
def create_video_from_images_and_audio(image_folder, audio_filename):
    image_files = sorted([os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(".jpg")])
    if not image_files:
        messagebox.showwarning("تحذير", "لا توجد صور لإنشاء الفيديو.")
        return

    clips = []
    duration_per_image = None

    if audio_filename and os.path.exists(audio_filename):
        audio_clip = AudioFileClip(audio_filename)
        total_duration = audio_clip.duration
        duration_per_image = total_duration / len(image_files)
    else:
        total_duration = len(image_files) * 3  # نفترض 3 ثواني لكل صورة
        duration_per_image = 3

    # إنشاء مقاطع الصور
    for img_path in image_files:
        img_clip = ImageSequenceClip([img_path], durations=[duration_per_image])
        clips.append(img_clip)

    video_clip = concatenate_videoclips(clips)

    if audio_filename and os.path.exists(audio_filename):
        video_clip = video_clip.set_audio(audio_clip)

    # تحديد مسار سطح المكتب
    desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    output_video_path = os.path.join(desktop_path, "final_video.mp4")

    video_clip.write_videofile(output_video_path, fps=24, codec="libx264", audio_codec="aac")

def create_content():
    gemini_api_key = gemini_entry.get()
    eleven_labs_api_key = eleven_entry.get()
    content_type = content_type_combo.get()

    script = generate_script_based_on_content_type(gemini_api_key, content_type)
    if not script:
        messagebox.showwarning("تحذير", "لا يوجد نص لتوليد المحتوى.")
        return

    cleaned_script = clean_script(script)

    # إنشاء التعليق الصوتي
    voiceover_filename = generate_voiceover(cleaned_script, eleven_labs_api_key)

    # استخراج المصطلحات الأساسية
    key_terms = extract_arabic_key_terms(cleaned_script)

    # تنزيل الصور
    total_images = 0
    for term in key_terms:
        download_images_from_bing(term, num_images=2, folder="visual")
        total_images += 2  # نفترض صورتين لكل مصطلح

    # إنشاء الفيديو
    try:
        create_video_from_images_and_audio("visual", voiceover_filename)
        messagebox.showinfo("نجاح", "تم إنشاء المحتوى بنجاح!")
    except Exception as e:
        messagebox.showerror("خطأ", f"حدث خطأ أثناء إنشاء الفيديو: {e}")
root.mainloop()
