"""
کد اصلاح شده سیستم تحلیل آزمون دانش‌آموزان کنکوری
"""

def calculate_percentage(correct, wrong, total):
    """
    محاسبه درصد آزمون با احتساب نمره منفی
    هر پاسخ صحیح: 3 امتیاز
    هر پاسخ غلط: -1 امتیاز
    حداکثر امتیاز ممکن: total * 3
    """
    score = (correct * 3) - (wrong * 1)
    max_possible_score = total * 3
    
    if max_possible_score == 0:
        return 0
    
    percentage = (score / max_possible_score) * 100
    
    # اگر درصد منفی شد، صفر برگردانیم
    return max(0, percentage)

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import random
from datetime import datetime

# برای تولید PDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.font_manager as font_manager
import numpy as np
import io
import os
from matplotlib.backends.backend_pdf import PdfPages
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.platypus import Image as ReportlabImage
from pathlib import Path

# تنظیم مسیر فایل فونت به دایرکتوری اصلی پروژه
BASE_DIR = Path(__file__).resolve().parent.parent
FONT_PATH = os.path.join(BASE_DIR, 'Vazir.ttf')  # فونت در دایرکتوری اصلی

# بررسی و نصب کتابخانه‌های مورد نیاز
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    ARABIC_SUPPORT = True
except ImportError:
    ARABIC_SUPPORT = False
    print("کتابخانه‌های arabic_reshaper و bidi نصب نیستند. متون فارسی ممکن است درست نمایش داده نشوند.")

# تنظیم فونت فارسی
def setup_persian_font():
    """تنظیم فونت فارسی برای matplotlib"""
    # بررسی وجود فونت فارسی
    if not os.path.exists(FONT_PATH):
        print(f"فونت فارسی در مسیر {FONT_PATH} یافت نشد.")
        return False
    
    try:
        # افزودن فونت به matplotlib
        font_prop = font_manager.FontProperties(fname=FONT_PATH)
        # تنظیم فونت به عنوان فونت پیش‌فرض
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False  # برای نمایش صحیح علامت منفی در متن فارسی
        return True
    except Exception as e:
        print(f"خطا در تنظیم فونت: {e}")
        return False

# فراخوانی تابع تنظیم فونت در زمان بارگذاری ماژول
setup_persian_font()

def fix_persian_text(text):
    """تصحیح متن فارسی برای نمایش در matplotlib"""
    if not ARABIC_SUPPORT:
        return text
    
    try:
        if isinstance(text, str):
            reshaped_text = arabic_reshaper.reshape(text)
            return get_display(reshaped_text)
        elif isinstance(text, list):
            return [fix_persian_text(t) for t in text]
        else:
            return text
    except Exception as e:
        print(f"خطا در تصحیح متن فارسی: {e}")
        return text

def create_radar_chart(data_dict, save_path=None):
    """
    ایجاد نمودار رادار برای نمایش 5 شاخص اصلی با پشتیبانی از فارسی
    """
    # محاسبه میانگین شاخص‌ها برای همه دروس
    all_indices = {
        'مدیریت ریسک': 0,
        'کارایی پاسخگویی': 0,
        'بهره‌وری مطالعه': 0,
        'اثربخشی تمرین': 0,
        'استفاده مؤثر از زمان': 0
    }
    count = 0
    
    for subject, data in data_dict.items():
        skill_indices = calculate_skill_indices(data)
        all_indices['مدیریت ریسک'] += skill_indices['risk_management']
        all_indices['کارایی پاسخگویی'] += skill_indices['answering_efficiency']
        all_indices['بهره‌وری مطالعه'] += skill_indices['study_productivity']
        all_indices['اثربخشی تمرین'] += skill_indices['practice_effectiveness']
        all_indices['استفاده مؤثر از زمان'] += skill_indices['time_utilization']
        count += 1
    
    # تبدیل میانگین شاخص‌ها به درصد
    if count > 0:
        for key in all_indices:
            all_indices[key] = all_indices[key] / count
    
    # نرمال‌سازی مقادیر شاخص‌های مختلف به مقیاس 0-100
    max_values = {
        'مدیریت ریسک': 100,       # از 0 تا 100
        'کارایی پاسخگویی': 100,   # از 0 تا 100
        'بهره‌وری مطالعه': 80,     # از 0 تا 80 (نرمال شده به 100)
        'اثربخشی تمرین': 10,      # از 0 تا 10 (نرمال شده به 100)
        'استفاده مؤثر از زمان': 30 # از 0 تا 30 (نرمال شده به 100)
    }
    
    normalized_indices = {}
    for key, value in all_indices.items():
        if key in max_values and max_values[key] > 0:
            normalized_indices[key] = min(100, value * 100 / max_values[key])
        else:
            normalized_indices[key] = value
    
    # ایجاد نمودار رادار
    categories = list(normalized_indices.keys())
    values = [normalized_indices[c] for c in categories]
    
    # اضافه کردن عنصر اول در انتها برای بستن نمودار
    values += values[:1]
    
    # اصلاح متن فارسی برای نمایش صحیح
    categories_fixed = [fix_persian_text(cat) for cat in categories]
    categories_fixed += categories_fixed[:1]  # اضافه کردن عنصر اول در انتها
    
    # زاویه‌ها برای هر دسته
    angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False)
    angles = np.append(angles, angles[0])  # بستن نمودار با تکرار اولین نقطه
    
    # ایجاد نمودار
    plt.figure(figsize=(10, 10), dpi=100)
    ax = plt.subplot(111, polar=True)
    
    # خط اصلی نمودار
    ax.plot(angles, values, 'o-', linewidth=2, color='#4361ee', label=fix_persian_text('شاخص‌های شما'))
    ax.fill(angles, values, alpha=0.25, color='#4361ee')
    
    # نمودار سطح متوسط (70%) برای مقایسه
    avg_values = [70] * len(values)
    ax.plot(angles, avg_values, 'o-', linewidth=1, color='#f44336', label=fix_persian_text('سطح مطلوب'))
    ax.fill(angles, avg_values, alpha=0.1, color='#f44336')
    
    # تنظیمات نمودار
    ax.set_thetagrids(angles[:-1] * 180/np.pi, categories_fixed[:-1])
    ax.set_ylim(0, 100)
    ax.grid(True)
    
    # عنوان و راهنما
    plt.title(fix_persian_text('نمودار شاخص‌های عملکردی'), size=15, pad=15)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # ذخیره نمودار در فایل
    if save_path:
        plt.savefig(save_path, format='png', dpi=100, bbox_inches='tight')
    
    plt.close()
    
    return save_path

def create_comparison_chart(data_dict, save_path=None):
    """
    ایجاد نمودار ستونی برای مقایسه درصدها بین دروس مختلف با پشتیبانی از فارسی
    """
    # استخراج داده‌ها
    subjects = list(data_dict.keys())
    percentages = [data_dict[s]['percentage'] for s in subjects]
    
    # اصلاح متن فارسی برای نمودار
    subjects_fixed = [fix_persian_text(s) for s in subjects]
    
    # ایجاد نمودار ستونی
    plt.figure(figsize=(12, 8), dpi=100)
    ax = plt.subplot(111)
    
    # رنگ‌های متفاوت برای هر درس
    colors = ['#4361ee', '#3f37c9', '#4cc9f0', '#4caf50', '#ff9800'][:len(subjects)]
    
    # ترسیم نمودار ستونی
    bars = ax.bar(subjects_fixed, percentages, color=colors, width=0.6)
    
    # افزودن برچسب‌ها
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{percentages[i]:.1f}%',
                ha='center', va='bottom', fontsize=12)
    
    # تنظیمات نمودار
    ax.set_ylim(0, max(100, max(percentages) * 1.1))
    ax.set_ylabel(fix_persian_text('درصد'), fontsize=14)
    ax.set_title(fix_persian_text('مقایسه درصد دروس'), fontsize=16)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # چرخش برچسب‌های محور X در صورت نیاز
    plt.xticks(rotation=45 if len(subjects) > 3 else 0)
    
    plt.tight_layout()
    
    # ذخیره نمودار در فایل
    if save_path:
        plt.savefig(save_path, format='png', dpi=100, bbox_inches='tight')
    
    plt.close()
    
    return save_path

def calculate_skill_indices(data):
    """محاسبه شاخص‌های مهارتی تست‌زنی براساس داده‌های آزمون"""
    
    # استخراج داده‌های لازم
    total = data['total']
    correct = data['correct']
    wrong = data['wrong']
    blank = data['blank']
    study_hours = data.get('study_hours', 0)  # با get برای سازگاری با داده‌های قدیمی
    practice = data.get('practice', 0)  # با get برای سازگاری با داده‌های قدیمی
    percentage = data['percentage']
    
    # شاخص 1: مدیریت ریسک - توانایی تشخیص سوالات مناسب برای پاسخگویی
    if total - blank > 0:  # اگر حداقل به یک سوال پاسخ داده باشد
        risk_management = (1 - (wrong / (total - blank))) * 100
    else:
        risk_management = 0
    
    # شاخص 2: کارایی پاسخگویی - استفاده بهینه از فرصت‌های کسب نمره
    denominator = correct + wrong + (blank * 0.3)
    if denominator > 0:
        answering_efficiency = (correct / denominator) * 100
    else:
        answering_efficiency = 0
    
    # شاخص 3: بهره‌وری مطالعه - میزان درصد به ازای هر ساعت مطالعه
    if study_hours > 0:
        study_productivity = (percentage / study_hours) * 10
    else:
        study_productivity = 0
    
    # شاخص 4: اثربخشی تمرین - میزان درصد به ازای هر تست تمرینی
    if practice > 0:
        practice_effectiveness = (percentage / practice) * 100
    else:
        practice_effectiveness = 0
    
    # شاخص 5: استفاده مؤثر از زمان - ترکیبی از زمان مطالعه و تعداد تست
    denominator_tue = study_hours + (practice / 20)
    if denominator_tue > 0:
        time_utilization = (percentage / denominator_tue) * 10
    else:
        time_utilization = 0
    
    return {
        'risk_management': round(risk_management, 1),
        'answering_efficiency': round(answering_efficiency, 1),
        'study_productivity': round(study_productivity, 1),
        'practice_effectiveness': round(practice_effectiveness, 1),
        'time_utilization': round(time_utilization, 1)
    }

def calculate_fuzzy_membership(value, low_thresh, high_thresh):
    """محاسبه درجه عضویت یک مقدار در مجموعه‌های فازی کم، متوسط و زیاد"""
    if value <= low_thresh:
        return {"low": 1.0, "medium": 0.0, "high": 0.0}
    elif value >= high_thresh:
        return {"low": 0.0, "medium": 0.0, "high": 1.0}
    elif value < (low_thresh + high_thresh) / 2:
        medium_degree = (value - low_thresh) / (high_thresh - low_thresh) * 2
        return {"low": 1.0 - medium_degree, "medium": medium_degree, "high": 0.0}
    else:
        high_degree = (value - (low_thresh + high_thresh) / 2) / (high_thresh - low_thresh) * 2
        return {"low": 0.0, "medium": 1.0 - high_degree, "high": high_degree}

def get_fuzzy_combined_feedback(risk, efficiency, spi, pei, tue, subjects_list=None):
    """تولید توصیه‌های ترکیبی بر اساس منطق فازی برای 5 شاخص با توجه به دروس کاربر"""
    # subjects_list: لیست دروسی که کاربر داده‌های آنها را وارد کرده است
    
    # محاسبه درجه عضویت هر شاخص در مجموعه‌های فازی
    risk_membership = calculate_fuzzy_membership(risk, 50, 75)
    efficiency_membership = calculate_fuzzy_membership(efficiency, 50, 75)
    spi_membership = calculate_fuzzy_membership(spi, 25, 50)
    pei_membership = calculate_fuzzy_membership(pei, 3, 6)
    tue_membership = calculate_fuzzy_membership(tue, 7, 15)
    
    # پایگاه قوانین فازی و توصیه‌های متناظر
    fuzzy_rules = []
    recommendations = []
    
    # استخراج سطوح غالب هر شاخص (با بیشترین درجه عضویت)
    dominant_risk = max(risk_membership, key=risk_membership.get)
    dominant_efficiency = max(efficiency_membership, key=efficiency_membership.get)
    dominant_spi = max(spi_membership, key=spi_membership.get)
    dominant_pei = max(pei_membership, key=pei_membership.get)
    dominant_tue = max(tue_membership, key=tue_membership.get)
    
    # بررسی حضور دروس خاص
    has_math = subjects_list and "ریاضیات" in subjects_list
    has_physics = subjects_list and "فیزیک" in subjects_list
    has_chemistry = subjects_list and "شیمی" in subjects_list
    has_biology = subjects_list and "زیست‌شناسی" in subjects_list
    
    # محاسبه درجه فعال‌سازی هر قانون (حداقل درجه عضویت در شرط‌ها)
    
    # قانون 1: عملکرد عالی در همه شاخص‌ها
    rule1_activation = min(
        risk_membership["high"],
        efficiency_membership["high"],
        spi_membership["high"],
        pei_membership["high"],
        tue_membership["high"]
    )
    
    if rule1_activation > 0:
        # توصیه‌های اختصاصی بر اساس دروس
        if has_math and has_physics:
            recommendation = "عملکرد شما در تمام شاخص‌ها عالی است. با توجه به تسلط شما در دروس ریاضی و فیزیک، می‌توانید روی مسائل ترکیبی تمرکز کنید که مفاهیم هر دو درس را به چالش می‌کشد. مفاهیم مشترک مانند مشتق و انتگرال در فیزیک را با رویکرد عمیق‌تری مطالعه کنید."
        elif has_biology and has_chemistry:
            recommendation = "عملکرد شما در تمام شاخص‌ها عالی است. با توجه به تسلط شما در دروس زیست‌شناسی و شیمی، روی مباحث بیوشیمی و واکنش‌های متابولیک تمرکز کنید. ارتباط بین این دو علم در سطح مولکولی فرصت‌های یادگیری عمیق‌تری را فراهم می‌کند."
        else:
            recommendation = "عملکرد شما در تمام شاخص‌ها عالی است. شما تعادل بسیار خوبی بین دقت، سرعت، بهره‌وری مطالعه و اثربخشی تمرین برقرار کرده‌اید. برای حفظ این سطح استثنایی، تکنیک 'یادگیری پیشرفته' را تمرین کنید: هر مبحث را یک بار به صورت سریع مرور، سپس تست‌های چالشی حل کرده، و در نهایت مفاهیم را به دیگران آموزش دهید."
        
        fuzzy_rules.append({
            "rule": "عملکرد عالی در همه شاخص‌ها",
            "activation": rule1_activation,
            "recommendation": recommendation
        })
    
    # قانون 2: مدیریت ریسک و کارایی پاسخگویی خوب اما بهره‌وری پایین
    rule2_activation = min(
        max(risk_membership["high"], risk_membership["medium"]),
        max(efficiency_membership["high"], efficiency_membership["medium"]),
        max(spi_membership["low"], pei_membership["low"], tue_membership["low"])
    )
    
    if rule2_activation > 0:
        if has_math:
            recommendation = "شما در آزمون‌دهی ریاضی عملکرد خوبی دارید، اما بهره‌وری مطالعه‌تان پایین است. تکنیک 'خط به خط' را پیاده کنید: هنگام مطالعه فرمول‌ها و اثبات‌ها، هر خط را کاملاً درک کنید قبل از رفتن به خط بعدی. همچنین برای هر تعریف یا قضیه، مثال‌های متنوع بررسی کنید."
        elif has_physics:
            recommendation = "شما در آزمون‌دهی فیزیک عملکرد خوبی دارید، اما بهره‌وری مطالعه‌تان پایین است. تکنیک 'مفهوم به فرمول' را پیاده کنید: ابتدا مفاهیم فیزیکی را به طور کامل درک کنید، سپس فرمول‌ها را به عنوان ابزاری برای بیان این مفاهیم یاد بگیرید، نه به عنوان قوانینی که باید حفظ شوند."
        elif has_chemistry:
            recommendation = "شما در آزمون‌دهی شیمی عملکرد خوبی دارید، اما بهره‌وری مطالعه‌تان پایین است. روش 'تجسم مولکولی' را اجرا کنید: با استفاده از مدل‌ها یا نرم‌افزارهای شیمی، ساختارهای مولکولی را تجسم کنید. درک فضایی از مولکول‌ها به یادگیری بهتر خواص و واکنش‌های آنها کمک می‌کند."
        elif has_biology:
            recommendation = "شما در آزمون‌دهی زیست‌شناسی عملکرد خوبی دارید، اما بهره‌وری مطالعه‌تان پایین است. تکنیک 'روایت علمی' را امتحان کنید: مفاهیم زیستی را به صورت داستان‌های علت و معلولی بیان کنید. این روش به خصوص برای فرآیندهای پیچیده مانند فتوسنتز یا تنفس سلولی بسیار مؤثر است."
        else:
            recommendation = "شما در تشخیص سوالات مناسب و پاسخگویی مؤثر مهارت خوبی دارید، اما در استفاده بهینه از زمان مطالعه و تمرین ضعف دارید. تکنیک 'برنامه‌ریزی متمرکز' را پیاده کنید: زمان مطالعه را به بلوک‌های 30 دقیقه‌ای تقسیم کنید که هر کدام شامل 20 دقیقه مطالعه عمیق، 5 دقیقه حل تست و 5 دقیقه جمع‌بندی باشد."
        
        fuzzy_rules.append({
            "rule": "مدیریت ریسک و کارایی پاسخگویی خوب اما بهره‌وری پایین",
            "activation": rule2_activation,
            "recommendation": recommendation
        })
    
    # قانون 3: بهره‌وری مطالعه و اثربخشی تمرین خوب اما مشکل در آزمون‌دهی
    rule3_activation = min(
        max(spi_membership["high"], spi_membership["medium"]),
        max(pei_membership["high"], pei_membership["medium"]),
        max(risk_membership["low"], efficiency_membership["low"])
    )
    
    if rule3_activation > 0:
        if has_math:
            recommendation = "شما در مطالعه و تمرین ریاضی بازدهی خوبی دارید، اما این دانش را در آزمون به خوبی به کار نمی‌گیرید. تکنیک 'تست زمان‌دار ریاضی' را اجرا کنید: هر روز 5 تست ریاضی را با زمان محدود حل کنید و آنها را عمیقاً تحلیل کنید. همچنین روی شناسایی الگوهای سوالات متمرکز شوید."
        elif has_physics:
            recommendation = "شما در مطالعه و تمرین فیزیک بازدهی خوبی دارید، اما این دانش را در آزمون به خوبی به کار نمی‌گیرید. روش 'ترجمه کلامی به فرمول' را تمرین کنید: برای هر سوال فیزیک، ابتدا اطلاعات را از متن استخراج کرده و به زبان فرمول‌ها ترجمه کنید. این مهارت در آزمون بسیار کمک‌کننده است."
        elif has_chemistry:
            recommendation = "شما در مطالعه و تمرین شیمی بازدهی خوبی دارید، اما این دانش را در آزمون به خوبی به کار نمی‌گیرید. تکنیک 'ترسیم سریع' را تمرین کنید: در سوالات شیمی، استفاده از ترسیم سریع واکنش‌ها یا ساختارها می‌تواند به تصمیم‌گیری دقیق‌تر کمک کند."
        elif has_biology:
            recommendation = "شما در مطالعه و تمرین زیست‌شناسی بازدهی خوبی دارید، اما این دانش را در آزمون به خوبی به کار نمی‌گیرید. تکنیک 'خودآزمون واژگان کلیدی' را امتحان کنید: فهرستی از واژگان کلیدی هر فصل تهیه کرده و خود را با آنها بیازمایید. بسیاری از سوالات زیست‌شناسی به درک دقیق واژگان متکی هستند."
        else:
            recommendation = "شما در مطالعه و تمرین بازدهی خوبی دارید، اما این دانش را در آزمون به خوبی به کار نمی‌گیرید. تکنیک 'شبیه‌سازی آزمون' را جدی بگیرید: هفته‌ای دو بار در شرایط کاملاً مشابه آزمون اصلی (از نظر زمان، محیط و استرس) تمرین کنید."
        
        fuzzy_rules.append({
            "rule": "بهره‌وری مطالعه و اثربخشی تمرین خوب اما مشکل در آزمون‌دهی",
            "activation": rule3_activation,
            "recommendation": recommendation
        })
    
    # قانون 4: مدیریت زمان خوب اما مشکل در سایر شاخص‌ها
    rule4_activation = min(
        tue_membership["high"],
        max(risk_membership["low"], efficiency_membership["low"], spi_membership["low"], pei_membership["low"])
    )
    
    if rule4_activation > 0:
        fuzzy_rules.append({
            "rule": "مدیریت زمان خوب اما مشکل در سایر شاخص‌ها",
            "activation": rule4_activation,
            "recommendation": "شما در مدیریت کلی زمان خود خوب عمل می‌کنید، اما این زمان به نتیجه مطلوب منجر نمی‌شود. "
            "تکنیک 'تمرکز بر کیفیت' را جایگزین 'تمرکز بر کمیت' کنید. به جای ساعت‌ها مطالعه کم‌بازده، با تکنیک 'مطالعه عمیق' پیش بروید: "
            "هر مبحث را با تمرکز کامل مطالعه کنید، مفاهیم کلیدی را استخراج نمایید، ارتباط بین مفاهیم را ترسیم کنید، و سپس تست‌های هدفمند حل کنید."
        })
    
    # قانون 5: بهره‌وری مطالعه خوب اما اثربخشی تمرین پایین
    rule5_activation = min(
        spi_membership["high"],
        pei_membership["low"]
    )
    
    if rule5_activation > 0:
        fuzzy_rules.append({
            "rule": "بهره‌وری مطالعه خوب اما اثربخشی تمرین پایین",
            "activation": rule5_activation,
            "recommendation": "شما مطالعه کارآمدی دارید، اما تمرین‌های شما اثربخشی کافی ندارند. استراتژی 'تمرین هدفمند' را پیاده کنید: "
            "به جای حل تعداد زیادی تست بدون هدف، ابتدا تست‌ها را دسته‌بندی کنید و از هر دسته نمونه‌های شاخص را حل کنید. "
            "همچنین تکنیک 'تحلیل عمیق' را به کار بگیرید: هر تست را کاملاً تجزیه کنید، تمام گزینه‌ها را بررسی کنید، و دلایل درستی یا نادرستی هر گزینه را یادداشت کنید."
        })
    
    # قانون 6: عملکرد متوسط در همه شاخص‌ها
    rule6_activation = min(
        risk_membership["medium"],
        efficiency_membership["medium"],
        spi_membership["medium"],
        pei_membership["medium"],
        tue_membership["medium"]
    )
    
    if rule6_activation > 0:
        fuzzy_rules.append({
            "rule": "عملکرد متوسط در همه شاخص‌ها",
            "activation": rule6_activation,
            "recommendation": "شما در تمام شاخص‌ها عملکرد متوسطی دارید. برای ارتقا به سطح بالاتر، استراتژی 'بهبود همه‌جانبه' را پیاده کنید: "
            "ابتدا یک 'نقشه راه سه ماهه' طراحی کنید که هر ماه روی بهبود دو شاخص تمرکز داشته باشد. "
            "برای ماه اول، تمرکز بر بهره‌وری مطالعه و اثربخشی تمرین، با استفاده از تکنیک 'یادگیری فعال' و 'تست‌زنی تحلیلی' می‌تواند نتایج سریعی به همراه داشته باشد."
        })
    
    # قانون 7: عملکرد ضعیف در همه شاخص‌ها
    rule7_activation = min(
        risk_membership["low"],
        efficiency_membership["low"],
        spi_membership["low"],
        pei_membership["low"],
        tue_membership["low"]
    )
    
    if rule7_activation > 0:
        fuzzy_rules.append({
            "rule": "عملکرد ضعیف در همه شاخص‌ها",
            "activation": rule7_activation,
            "recommendation": "نتایج نشان می‌دهد در تمام شاخص‌ها نیاز به بهبود جدی دارید. استراتژی 'بازسازی بنیادی' را شروع کنید: "
            "ابتدا از یک مشاور تحصیلی کمک بگیرید تا سبک یادگیری شما را شناسایی کند. سپس یک برنامه مطالعاتی کاملاً جدید با تمرکز بر مفاهیم پایه طراحی کنید. "
            "تکنیک 'تکرار و تمرین روزانه' را پیاده کنید: هر روز حداقل 2 ساعت با تمرکز کامل مطالعه کنید و 10 تست با تحلیل دقیق حل نمایید. "
            "نتایج را هفتگی بررسی کنید و مطابق با پیشرفت خود، برنامه را تنظیم نمایید."
        })
    
    # قانون 8: سرعت پاسخگویی خوب اما دقت پایین
    rule8_activation = min(
        risk_membership["low"],
        efficiency_membership["high"]
    )
    
    if rule8_activation > 0:
        fuzzy_rules.append({
            "rule": "سرعت پاسخگویی خوب اما دقت پایین",
            "activation": rule8_activation,
            "recommendation": "شما سریع پاسخ می‌دهید، اما اغلب انتخاب‌های نادرستی دارید. تکنیک 'تأمل قبل از پاسخ' را تمرین کنید: "
            "قبل از هر پاسخ، 5 ثانیه فکر کنید و به خود یادآوری کنید که هر پاسخ غلط، امتیاز منفی دارد. "
            "همچنین استراتژی 'شناسایی تله‌ها' را یاد بگیرید: الگوهای سوالات فریبنده را شناسایی کرده و تکنیک‌های خاص برای مقابله با آنها را تمرین کنید."
        })
    
    # قانون 9: بهره‌وری پایین و استفاده ناکارآمد از زمان
    rule9_activation = min(
        spi_membership["low"],
        tue_membership["low"]
    )
    
    if rule9_activation > 0:
        fuzzy_rules.append({
            "rule": "بهره‌وری پایین و استفاده ناکارآمد از زمان",
            "activation": rule9_activation,
            "recommendation": "شما در استفاده مؤثر از زمان مطالعه مشکل دارید. استراتژی 'مطالعه ساختاریافته' را پیاده کنید: "
            "زمان مطالعه را به بخش‌های کوچک‌تر تقسیم کنید و برای هر بخش هدف مشخصی تعیین کنید. "
            "از تکنیک 'نقشه مفهومی' و 'خلاصه‌نویسی فعال' استفاده کنید و پس از هر جلسه مطالعه، 5 دقیقه به ارزیابی میزان دستیابی به اهداف بپردازید. "
            "همچنین 'اتلاف‌کننده‌های زمان' را شناسایی و محدود کنید."
        })
    
    # قانون 10: مدیریت ریسک خوب اما کارایی پاسخگویی پایین
    rule10_activation = min(
        risk_membership["high"],
        efficiency_membership["low"]
    )
    
    if rule10_activation > 0:
        fuzzy_rules.append({
            "rule": "مدیریت ریسک خوب اما کارایی پاسخگویی پایین",
            "activation": rule10_activation,
            "recommendation": "شما به درستی می‌دانید به کدام سوالات پاسخ دهید، اما زمان زیادی را صرف تصمیم‌گیری می‌کنید. "
            "تکنیک '30 ثانیه اول' را امتحان کنید: در 30 ثانیه اول مشخص کنید آیا سوال را می‌دانید یا خیر. "
            "همچنین الگوریتم‌های ذهنی برای پاسخگویی سریع طراحی کنید: مثلاً در سوالات چهارگزینه‌ای، ابتدا گزینه‌های نادرست را حذف کنید تا به پاسخ برسید."
        })
    
    # مرتب‌سازی قوانین بر اساس درجه فعال‌سازی
    fuzzy_rules.sort(key=lambda x: x["activation"], reverse=True)
    
    # انتخاب 3 قانون برتر برای توصیه
    for rule in fuzzy_rules[:3]:
        recommendations.append(rule["recommendation"])
    
    # اگر هیچ قانونی فعال نشده باشد
    if not recommendations:
        # توصیه پیش‌فرض بر اساس سطوح غالب هر شاخص
        default_recommendation = f"بر اساس تحلیل شاخص‌های شما (مدیریت ریسک: {dominant_risk}، کارایی پاسخگویی: {dominant_efficiency}، " \
                              f"بهره‌وری مطالعه: {dominant_spi}، اثربخشی تمرین: {dominant_pei}، استفاده مؤثر از زمان: {dominant_tue})، " \
                              f"پیشنهاد می‌شود روی بهبود جنبه‌های ضعیف‌تر تمرکز کنید و از نقاط قوت خود استفاده کنید."
        recommendations.append(default_recommendation)
    
    return recommendations

def dashboard(request):
    return render(request, 'analyzer/dashboard.html')

@csrf_exempt
def save_result(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # محاسبه مجدد درصد با در نظر گرفتن نمره منفی
            correct = data['correct']
            wrong = data['wrong']
            total = data['total']
            data['percentage'] = calculate_percentage(correct, wrong, total)
            
            # محاسبه سوالات بی‌پاسخ
            blank = total - (correct + wrong)
            data['blank'] = blank
            
            # محاسبه شاخص‌های مهارتی - همه 5 شاخص
            skill_indices = calculate_skill_indices({
                'total': total, 
                'correct': correct, 
                'wrong': wrong, 
                'blank': blank,
                'study_hours': data.get('study_hours', 0),
                'practice': data.get('practice', 0),
                'percentage': data['percentage']
            })
            
            # افزودن شاخص‌ها به داده‌ها
            data.update(skill_indices)
            
            # در حالت واقعی باید داده‌ها را در دیتابیس ذخیره کنیم
            # اما برای سادگی فعلاً فقط در session ذخیره می‌کنیم
            if 'test_results' not in request.session:
                request.session['test_results'] = {}
            
            request.session['test_results'][data['subject']] = data
            request.session.modified = True
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
def generate_report(request):
    """تولید گزارش ساده به جای PDF پیچیده"""
    if 'test_results' not in request.session or not request.session['test_results']:
        return HttpResponse("لطفاً ابتدا اطلاعات تست‌ها را وارد کنید.")
    
    # نمایش نتایج به صورت HTML ساده
    html_output = "<html dir='rtl'><head><title>گزارش آزمون</title>"
    html_output += "<meta charset='utf-8'>"
    html_output += "<style>body {font-family: 'Tahoma', sans-serif; margin: 20px;} table {width: 100%; border-collapse: collapse;} th, td {padding: 8px; text-align: right; border: 1px solid #ddd;} th {background-color: #f2f2f2;}</style>"
    html_output += "</head><body>"
    
    html_output += "<h1>گزارش تحلیلی عملکرد آزمون</h1>"
    
    # خلاصه نتایج
    html_output += "<h2>خلاصه نتایج:</h2>"
    
    # محاسبه میانگین کلی
    avg_percentage = sum(data['percentage'] for data in request.session['test_results'].values()) / len(request.session['test_results'])
    
    html_output += "<table>"
    html_output += "<tr><th>مورد</th><th>مقدار</th></tr>"
    html_output += f"<tr><td>تعداد دروس</td><td>{len(request.session['test_results'])}</td></tr>"
    html_output += f"<tr><td>میانگین درصد</td><td>{avg_percentage:.1f}%</td></tr>"
    html_output += "</table>"
    
    # بخش تحلیل هر درس
    html_output += "<h2>تحلیل هر درس:</h2>"
    
    for subject, data in request.session['test_results'].items():
        html_output += f"<h3>درس {subject}:</h3>"
        
        html_output += "<table>"
        html_output += "<tr><th>مورد</th><th>مقدار</th></tr>"
        html_output += f"<tr><td>درصد</td><td>{data['percentage']:.1f}%</td></tr>"
        html_output += f"<tr><td>تعداد سوالات</td><td>{data['total']}</td></tr>"
        html_output += f"<tr><td>پاسخ صحیح</td><td>{data['correct']}</td></tr>"
        html_output += f"<tr><td>پاسخ غلط</td><td>{data['wrong']}</td></tr>"
        html_output += f"<tr><td>بی‌پاسخ</td><td>{data['blank']}</td></tr>"
        html_output += "</table>"
    
    html_output += "</body></html>"
    
    return HttpResponse(html_output)
def get_status_text(value, thresholds):
    """تعیین وضعیت هر شاخص بر اساس آستانه‌ها"""
    if value >= thresholds[2]:
        return "عالی"
    elif value >= thresholds[1]:
        return "خوب"
    elif value >= thresholds[0]:
        return "متوسط"
    else:
        return "نیازمند بهبود"