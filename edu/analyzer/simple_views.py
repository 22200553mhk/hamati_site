from django.shortcuts import render
from django.http import HttpResponse

def dashboard(request):
    """داشبورد اصلی با قالب HTML"""
    # اگر reset_data در پارامترهای URL باشد، داده‌های قبلی را پاک می‌کنیم
    if 'reset_data' in request.GET:
        if 'test_results' in request.session:
            del request.session['test_results']
            request.session.modified = True
    
    # ممکن است مشکل در اسکریپت JavaScript باشد، پس یک نسخه ساده‌تر از آن را ارائه می‌دهیم
    context = {
        'extra_js': """
        <script>
        // پاک کردن localStorage در هر بار بارگذاری صفحه
        document.addEventListener('DOMContentLoaded', function() {
            const subjects = ['ریاضیات', 'فیزیک', 'شیمی', 'زیست‌شناسی'];
            subjects.forEach(subject => {
                localStorage.removeItem(`${subject}_saved`);
            });
            
            // به‌روزرسانی نوار پیشرفت
            updateProgress();
        });
        </script>
        """
    }
    
    return render(request, 'analyzer/dashboard.html', context)
    
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import datetime
def calculate_percentage(correct, wrong, total):
    """محاسبه درصد آزمون با احتساب نمره منفی"""
    score = (correct * 3) - (wrong * 1)
    max_possible_score = total * 3
    
    if max_possible_score == 0:
        return 0
    
    percentage = (score / max_possible_score) * 100
    return max(0, percentage)

@csrf_exempt
def save_result(request):
    """ذخیره نتایج آزمون"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # محاسبه درصد
            correct = int(data.get('correct', 0))
            wrong = int(data.get('wrong', 0))
            total = int(data.get('total', 0))
            study_hours = float(data.get('study_hours', 0))
            practice = int(data.get('practice', 0))
            
            data['percentage'] = calculate_percentage(correct, wrong, total)
            
            # محاسبه سوالات بی‌پاسخ
            blank = total - (correct + wrong)
            data['blank'] = blank
            
            # محاسبه شاخص‌ها
            risk_management = 0
            if total - blank > 0:
                risk_management = (1 - (wrong / (total - blank))) * 100
                
            answering_efficiency = 0
            denominator = correct + wrong + (blank * 0.3)
            if denominator > 0:
                answering_efficiency = (correct / denominator) * 100
                
            study_productivity = 0
            if study_hours > 0:
                study_productivity = (data['percentage'] / study_hours) * 10
                
            practice_effectiveness = 0
            if practice > 0:
                practice_effectiveness = (data['percentage'] / practice) * 100
                
            time_utilization = 0
            denominator_tue = study_hours + (practice / 20)
            if denominator_tue > 0:
                time_utilization = (data['percentage'] / denominator_tue) * 10
            
            # افزودن شاخص‌ها به داده‌ها
            data.update({
                'risk_management': round(risk_management, 1),
                'answering_efficiency': round(answering_efficiency, 1),
                'study_productivity': round(study_productivity, 1),
                'practice_effectiveness': round(practice_effectiveness, 1),
                'time_utilization': round(time_utilization, 1)
            })
            
            # ذخیره در session
            if 'test_results' not in request.session:
                request.session['test_results'] = {}
            
            # ذخیره با کلید درس
            subject = data.get('subject', 'درس نامشخص')
            request.session['test_results'][subject] = data
            request.session.modified = True
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return JsonResponse({
                'status': 'error', 
                'message': str(e),
                'detail': error_detail
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
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
def generate_subject_feedback(subject, data):
    """تولید توصیه‌های شخصی‌سازی شده برای هر درس با تحلیل دقیق داده‌های دانش‌آموز"""
    feedback = []
    
    # استخراج داده‌های دقیق برای استفاده در توصیه‌ها
    percentage = round(data['percentage'], 1)
    correct = data['correct']
    wrong = data['wrong']
    blank = data['blank']
    total = data['total']
    study_hours = data['study_hours']
    practice = data['practice']
    risk = round(data['risk_management'], 1)
    efficiency = round(data['answering_efficiency'], 1)
    productivity = round(data['study_productivity'], 1)
    
    # 1. تحلیل و توصیه بر اساس مدیریت ریسک
    if data['risk_management'] < 50:
        if subject == "ریاضیات":
            feedback.append(f"با توجه به مدیریت ریسک {risk}% شما در ریاضی و نسبت {wrong} پاسخ غلط به {correct} پاسخ صحیح، پیشنهاد می‌شود از «تکنیک دسته‌بندی هوشمند» استفاده کنید: در آزمون بعدی، سوالات را با علامت‌گذاری شخصی به سه دسته «اطمینان کامل»، «نسبتاً مطمئن» و «نامطمئن» تقسیم کنید و فقط به دو دسته اول پاسخ دهید. این روش با الگوی پاسخ‌دهی فعلی شما، می‌تواند درصدتان را حداقل 15% افزایش دهد.")
        elif subject == "فیزیک":
            feedback.append(f"با بررسی عملکرد شما در فیزیک، مدیریت ریسک {risk}% نشان می‌دهد که از هر 5 سوالی که پاسخ می‌دهید، تقریباً به {round(5*(wrong/(correct+wrong)))} سوال پاسخ اشتباه می‌دهید. برای شما که در هر ساعت مطالعه {round(productivity, 1)} درصد بهره‌وری دارید، «روش شناسایی سریع 30 ثانیه‌ای» مناسب است: برای هر سوال فقط 30 ثانیه وقت بگذارید تا تشخیص دهید قابل حل است یا خیر، و سپس تصمیم بگیرید.")
        else:
            feedback.append(f"تحلیل مدیریت ریسک {risk}% شما در درس {subject} و الگوی {correct} پاسخ صحیح، {wrong} پاسخ غلط و {blank} سوال بی‌پاسخ نشان می‌دهد که باید استراتژی پاسخ‌دهی خود را تغییر دهید. با توجه به سبک یادگیری شما (مطالعه {study_hours} ساعت و تمرین {practice} تست)، «روش 3-2-1» پیشنهاد می‌شود: 3 دور سوالات را مرور کنید، 2 بار اطمینان خود را بسنجید و تنها به 1 دسته از سوالات که کاملاً مطمئن هستید پاسخ دهید.")
    else:
        if subject == "ریاضیات":
            feedback.append(f"مدیریت ریسک {risk}% شما در ریاضی نشان‌دهنده قدرت تشخیص خوب شماست. با توجه به الگوی پاسخگویی شما ({correct} صحیح و {wrong} غلط)، اکنون می‌توانید «تکنیک چالش‌پذیری» را امتحان کنید: در هر آزمون، تعداد 3 سوال دشوارتر از سطح معمول خود را انتخاب و تلاش کنید پاسخ دهید. این تمرین با توجه به توانایی بالای شما در انتخاب سوالات مناسب، مرز دانش شما را گسترش می‌دهد.")
        else:
            feedback.append(f"مدیریت ریسک {risk}% شما در {subject} بسیار خوب است! تحلیل پاسخ‌های شما نشان می‌دهد از هر 10 سوالی که انتخاب می‌کنید، به {10*correct/(correct+wrong):.1f} سوال به درستی پاسخ می‌دهید. با این دقت، پیشنهاد می‌شود «استراتژی سرعت‌بخشی» را اجرا کنید: زمان پاسخگویی به هر سوال را 20% کاهش دهید، بدون اینکه دقت‌تان افت کند. با توجه به شناختی که از توانایی‌های خود پیدا کرده‌اید، این استراتژی می‌تواند باعث افزایش قابل توجه نمره شما شود.")
    
    # 2. تحلیل و توصیه بر اساس بهره‌وری مطالعه
    if data['study_productivity'] < 30:
        if subject == "ریاضیات":
            feedback.append(f"بهره‌وری مطالعه {productivity} شما در ریاضی نشان می‌دهد برای هر 1% پیشرفت، تقریباً {1/productivity:.1f} ساعت زمان صرف می‌کنید. با توجه به الگوی یادگیری شما (مطالعه {study_hours} ساعت در هفته)، «تکنیک جزیره‌ای» برای شما طراحی شده است: مطالعه را به جزیره‌های 25 دقیقه‌ای تقسیم کنید، هر جزیره را به یک مبحث خاص اختصاص دهید، و بلافاصله پس از مطالعه، 2 تست مرتبط حل کنید. این روش می‌تواند بهره‌وری شما را تا 40% افزایش دهد.")
        elif subject == "فیزیک":
            feedback.append(f"تحلیل بهره‌وری {productivity} شما در فیزیک با {study_hours} ساعت مطالعه و درصد {percentage}% نشان می‌دهد شیوه مطالعه شما کارآمد نیست. با توجه به تعداد {total} سوال آزمون شما، «روش PEC» (پیش‌بینی، توضیح، اتصال) پیشنهاد می‌شود: قبل از مطالعه هر مفهوم، نتیجه را پیش‌بینی کنید، سپس آن را برای خودتان توضیح دهید، و در نهایت به مفاهیم قبلی متصل کنید. این روش با سبک یادگیری شما سازگار است و می‌تواند زمان یادگیری را 30% کاهش دهد.")
        else:
            feedback.append(f"بهره‌وری مطالعه {productivity} در درس {subject} با توجه به {study_hours} ساعت مطالعه هفتگی شما بسیار پایین است. تحلیل عملکرد شما نشان می‌دهد احتمالاً اطلاعات را به صورت پراکنده ذخیره می‌کنید. «تکنیک مطالعه ساختاریافته 3R» برای شما طراحی شده است: Read (15 دقیقه بخوانید)، Recall (بدون نگاه کردن به متن، مطالب را بازگو کنید)، Review (مجدداً مرور کنید). این تکنیک مناسب نیمکره غالب مغز شماست و می‌تواند بهره‌وری را دو برابر کند.")
    else:
        if subject == "ریاضیات":
            feedback.append(f"بهره‌وری مطالعه {productivity} شما در ریاضی قابل توجه است! با {study_hours} ساعت مطالعه هفتگی، شما به درصد {percentage}% رسیده‌اید. برای دستیابی به سطح بالاتر، «تکنیک بازخورد فعال» برای شما طراحی شده است: پس از هر جلسه مطالعه، 5 دقیقه وقت بگذارید و دقیقاً مشخص کنید چه چیزی یاد گرفته‌اید و چه چیزی هنوز نیاز به کار دارد. سپس با نگاه به درصد فعلی، هدف بعدی را 5% بالاتر تعیین کنید. این روش با سبک یادگیری تحلیلی شما هماهنگ است.")
        else:
            feedback.append(f"با بهره‌وری مطالعه {productivity} در درس {subject}، شما جزو 20% برتر دانش‌آموزان با بهره‌وری بالا هستید! با توجه به الگوی موفقیت شما ({correct} پاسخ صحیح از {total} سوال)، «استراتژی آموزش معکوس» برای شما طراحی شده است: مفاهیمی که کاملاً فرا گرفته‌اید را به دیگران آموزش دهید، حتی اگر مخاطب فرضی باشد. این روش به تثبیت دانش و کشف خلاءهای احتمالی یادگیری شما کمک می‌کند و با سبک یادگیری شما کاملاً همخوانی دارد.")
    
    # 3. تحلیل و توصیه بر اساس درصد کلی
    if data['percentage'] < 30:
        if subject == "ریاضیات":
            feedback.append(f"درصد {percentage}% شما در ریاضی با {correct} پاسخ صحیح و {wrong} پاسخ غلط نشان می‌دهد احتمالاً در مفاهیم پایه‌ای مشکل دارید. با توجه به ساعات مطالعه ({study_hours} ساعت) و تعداد تست‌ها ({practice} تست)، «برنامه بازسازی پایه ۲۱ روزه» برای شما طراحی شده است: روزانه فقط 30 دقیقه روی مفاهیم اولیه (جبر پایه، معادلات درجه اول و هندسه مقدماتی) کار کنید و سپس 5 تست ساده حل کنید. پس از 3 هفته، آزمون مجدد نشان خواهد داد درصدتان به حدود 45% رسیده است.")
        elif subject == "فیزیک":
            feedback.append(f"تحلیل درصد {percentage}% شما در فیزیک با {wrong} پاسخ اشتباه نشان می‌دهد درک مفهومی شما از اصول اولیه ضعیف است. برای شما که {study_hours} ساعت مطالعه می‌کنید، «روش مدل‌سازی مفهومی» طراحی شده است: فیزیک را بدون فرمول‌ها شروع کنید؛ هر مفهوم را با یک تصویر و مثال واقعی درک کنید. مثلاً برای نیرو، تصور کنید دارید یک جسم را هل می‌دهید. این روش با سبک یادگیری بصری شما مطابقت دارد و می‌تواند درصدتان را در مدت 4 هفته دو برابر کند.")
        else:
            feedback.append(f"درصد {percentage}% شما در {subject} با {correct} پاسخ درست از {total} سوال نشان می‌دهد نیاز به یک برنامه کاملاً متفاوت دارید. با تحلیل عملکرد شما، «استراتژی پله‌ای 4×4» برای وضعیت شما طراحی شده است: ابتدا فقط 4 مبحث پایه‌ای را انتخاب کنید، روزانه 4 صفحه بخوانید، 4 سوال ساده حل کنید و هر 4 روز یکبار خودآزمایی کنید. تعهد به این برنامه ساده اما منظم، با توجه به سبک یادگیری تدریجی شما، درصدتان را در 8 هفته به بیش از 40% می‌رساند.")
    elif data['percentage'] >= 30 and data['percentage'] < 70:
        if subject == "ریاضیات":
            feedback.append(f"با درصد {percentage}% در ریاضی، شما پتانسیل زیادی برای پیشرفت دارید. تحلیل {correct} پاسخ صحیح و {wrong} پاسخ غلط شما نشان می‌دهد در برخی مباحث قوی و در برخی ضعیف هستید. «برنامه تقویت نقاط ضعف» برای شما: ابتدا سوالات آزمون را بر اساس موضوع دسته‌بندی کنید، مباحثی که درصد موفقیت کمتر از 40% دارید را شناسایی کنید، و زمان مطالعه را دو برابر روی این مباحث متمرکز کنید. با توجه به سبک یادگیری تحلیلی شما، این روش می‌تواند درصدتان را در مدت 6 هفته به بالای 60% برساند.")
        else:
            feedback.append(f"درصد {percentage}% شما در {subject} با نسبت {correct} به {total} نشان‌دهنده پتانسیل قابل توجه شماست. با توجه به مطالعه {study_hours} ساعتی و تمرین {practice} تست هفتگی، «روش شکاف‌یابی» برای شما طراحی شده است: سوالات پاسخ نداده و غلط را براساس موضوع دسته‌بندی کنید، 3 مبحث با بیشترین ضعف را شناسایی کنید، و برای هر کدام یک «برگه فرمول/مفهوم» تهیه کنید که همیشه همراهتان باشد. این روش با توجه به سبک یادگیری شما، می‌تواند درصدتان را تا 20% افزایش دهد.")
    else:
        if subject == "ریاضیات":
            feedback.append(f"درصد عالی {percentage}% شما در ریاضی با {correct} پاسخ صحیح از {total} سوال، نشان‌دهنده تسلط شماست! برای حفظ این برتری و پیشرفت بیشتر، «استراتژی المپیادی نرم» برای شما طراحی شده است: در هر مبحثی که تسلط دارید (بیش از 80% سوالات را درست پاسخ می‌دهید)، یک سوال چالشی المپیادی حل کنید. این کار به شما کمک می‌کند با حفظ اعتماد به نفس، ذهنتان را برای سوالات غیرمعمول آماده کنید. با این روش که متناسب با سبک تفکر عمیق شماست، می‌توانید به درصدهای بالای 90% برسید.")
        else:
            feedback.append(f"درصد استثنایی {percentage}% شما در {subject} با {correct} پاسخ صحیح نشانگر تسلط شماست. تحلیل عملکردتان در کنار {study_hours} ساعت مطالعه و {practice} تست تمرینی نشان می‌دهد که آماده هستید به مرحله بعدی بروید. «روش تدریس خلاقانه» برای شما طراحی شده است: مباحثی که کاملاً مسلط هستید را به شیوه‌ای خلاقانه (مثل ساخت ویدیو، نوشتن خلاصه تصویری، یا آموزش به دوستان) تدریس کنید. این روش که با سبک یادگیری فعال شما هماهنگ است، باعث می‌شود درک عمیق‌تری پیدا کنید و همزمان، مطالب در ذهنتان ماندگارتر شود.")
    
    return feedback
def generate_report(request):
    """تولید گزارش HTML با نمودارها و قابلیت تبدیل به PDF"""
    if 'test_results' not in request.session or not request.session['test_results']:
        return HttpResponse("لطفاً ابتدا اطلاعات تست‌ها را وارد کنید.")
    
    # نمایش نتایج به صورت HTML ساده
    html_output = "<html dir='rtl'><head><title>گزارش آزمون</title>"
    html_output += "<meta charset='utf-8'>"
    
    # اضافه کردن Font Awesome برای آیکون‌ها
    html_output += """<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">"""
    
    # اضافه کردن Chart.js برای نمودارها
    html_output += """<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>"""
    
    # اضافه کردن jsPDF برای تبدیل به PDF
    html_output += """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    function generatePDF() {
        // مخفی کردن موقت نوار کنترل‌ها
        document.getElementById('pdfButton').style.display = 'none';
        document.getElementById('loading').style.display = 'inline-block';
        
        const { jsPDF } = window.jspdf;
        
        // تنظیم اندازه و جهت صفحه
        const pdf = new jsPDF('p', 'mm', 'a4');
        
        // گرفتن محتوای گزارش
        const reportContent = document.getElementById('reportContent');
        
        // استفاده از html2canvas برای تبدیل محتوا به تصویر
        html2canvas(reportContent, {
            scale: 2,  // کیفیت بالاتر
            useCORS: true,
            logging: false
        }).then(canvas => {
            // محاسبه اندازه‌ها برای حالت پرتره
            const imgWidth = 210; // عرض A4 به میلی‌متر
            const pageHeight = 295;  // ارتفاع A4 به میلی‌متر
            const imgHeight = canvas.height * imgWidth / canvas.width;
            
            // اضافه کردن تصویر به PDF
            let heightLeft = imgHeight;
            let position = 0;
            let pageData = canvas.toDataURL('image/jpeg', 1.0);
            
            pdf.addImage(pageData, 'JPEG', 0, position, imgWidth, imgHeight);
            heightLeft -= pageHeight;

            // اگر محتوا بیشتر از یک صفحه باشد، صفحات بیشتری اضافه می‌کنیم
            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(pageData, 'JPEG', 0, position, imgWidth, imgHeight);
                heightLeft -= pageHeight;
            }
            
            // دانلود PDF
            pdf.save('گزارش_آزمون.pdf');
            
            // نمایش دوباره دکمه
            document.getElementById('pdfButton').style.display = 'inline-block';
            document.getElementById('loading').style.display = 'none';
        });
    }
    </script>
    """
    
    # استایل‌های زیبا و مدرن
    html_output += """
    <style>
        body {
            font-family: 'Vazir', 'Tahoma', sans-serif; 
            margin: 0; 
            padding: 0;
            background-color: #f5f7ff;
            line-height: 1.6;
            color: #333;
        }
        
        #reportContent {
            background-color: white;
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin: 20px;
            max-width: 1200px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .report-header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #e0e6ff;
            padding-bottom: 20px;
        }
        
        h1, h2, h3, h4 {
            color: #3a36e0;
            font-weight: 700;
        }
        
        h1 {
            font-size: 28px;
            margin-bottom: 10px;
        }
        
        h2 {
            font-size: 22px;
            margin-top: 30px;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 1px solid #e0e6ff;
        }
        
        h3 {
            font-size: 18px;
            margin-top: 25px;
            background-color: #f0f4ff;
            padding: 10px 15px;
            border-radius: 8px;
        }
        
        h4 {
            font-size: 16px;
            margin-top: 20px;
            color: #4361ee;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 25px;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
        }
        
        th, td {
            padding: 12px 15px;
            text-align: right;
        }
        
        th {
            background: linear-gradient(135deg, #4361ee, #3a36e0);
            color: white;
            font-weight: bold;
        }
        
        tr:nth-child(even) {
            background-color: #f6f8ff;
        }
        
        tr:hover {
            background-color: #eef2ff;
        }
        
        .tip {
            background-color: #f0f8ff;
            padding: 15px 20px;
            border-right: 5px solid #4361ee;
            margin: 15px 0;
            border-radius: 8px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }
        
        .tip:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
        }
        
        .tip h3 {
            background: none;
            color: #3a36e0;
            margin-top: 0;
            padding: 0;
            margin-bottom: 10px;
        }
        
        .chart-container {
            width: 100%;
            max-width: 800px;
            margin: 30px auto;
            height: 400px;
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.08);
        }
        
        .button {
            display: inline-block;
            padding: 12px 25px;
            background: linear-gradient(135deg, #4361ee, #3a36e0);
            color: white;
            text-decoration: none;
            border-radius: 50px;
            cursor: pointer;
            border: none;
            font-family: 'Vazir', 'Tahoma', sans-serif;
            font-size: 14px;
            margin: 5px;
            box-shadow: 0 3px 10px rgba(67, 97, 238, 0.3);
            transition: all 0.3s ease;
        }
        
        .button:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(67, 97, 238, 0.4);
            background: linear-gradient(135deg, #3a36e0, #2d2bb6);
        }
        
        #loading {
            display: none;
            margin-right: 10px;
        }
        
        .summary-boxes {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .summary-box {
            flex: 1;
            min-width: 200px;
            background: linear-gradient(135deg, #ffffff, #f6f8ff);
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
            text-align: center;
        }
        
        .summary-box .value {
            font-size: 24px;
            font-weight: bold;
            color: #3a36e0;
            margin: 10px 0;
        }
        
        .summary-box .label {
            color: #666;
            font-size: 14px;
        }
        
        .subject-section {
            background-color: white;
            border-radius: 10px;
            margin-bottom: 25px;
            padding: 20px;
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.05);
        }
        
        .subject-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .subject-title {
            font-size: 20px;
            color: #3a36e0;
            margin: 0;
        }
        
        .subject-percentage {
            font-size: 18px;
            font-weight: bold;
            color: white;
            background: linear-gradient(135deg, #4361ee, #3a36e0);
            padding: 5px 15px;
            border-radius: 20px;
        }
        
        @media print {
            .no-print {
                display: none;
            }
            
            body, #reportContent {
                background-color: white;
                box-shadow: none;
                margin: 0;
                padding: 10px;
            }
        }
    </style>
    """
    
    html_output += "</head><body>"
    
    # دکمه دانلود PDF در بالای صفحه - طراحی مدرن
    html_output += """
    <div class="no-print" style="text-align: center; margin-bottom: 20px; padding: 20px; background-color: white; border-radius: 15px; box-shadow: 0 3px 15px rgba(0, 0, 0, 0.08);">
        <button id="pdfButton" class="button" onclick="generatePDF()">
            <i class="fas fa-file-pdf" style="margin-left: 8px;"></i>
            دانلود PDF
        </button>
        <span id="loading" style="display: none; margin-right: 10px;">
            <i class="fas fa-spinner fa-spin"></i>
            در حال تولید PDF...
        </span>
    </div>
    """
    
    # محتوای گزارش در یک div جداگانه - طراحی مدرن
    html_output += "<div id='reportContent'>"
    
    # سربرگ گزارش
    html_output += """
    <div class="report-header">
        <h1>گزارش تحلیلی عملکرد آزمون</h1>
        <p>تاریخ: """ + datetime.now().strftime("%Y/%m/%d") + """</p>
    </div>
    """
    
    # خلاصه نتایج - طراحی مدرن
    html_output += "<h2>خلاصه نتایج</h2>"
    
    # محاسبه میانگین کلی
    avg_percentage = sum(data['percentage'] for data in request.session['test_results'].values()) / len(request.session['test_results'])
    
    # نمایش خلاصه در باکس‌های جذاب
    html_output += """
    <div class="summary-boxes">
        <div class="summary-box">
            <div class="label">تعداد دروس</div>
            <div class="value">""" + str(len(request.session['test_results'])) + """</div>
        </div>
        <div class="summary-box">
            <div class="label">میانگین درصد</div>
            <div class="value">""" + f"{avg_percentage:.1f}%" + """</div>
        </div>
        <div class="summary-box">
            <div class="label">تعداد کل سوالات</div>
            <div class="value">""" + str(sum(data['total'] for data in request.session['test_results'].values())) + """</div>
        </div>
        <div class="summary-box">
            <div class="label">پاسخ‌های صحیح</div>
            <div class="value">""" + str(sum(data['correct'] for data in request.session['test_results'].values())) + """</div>
        </div>
    </div>
    """
    
    # نمودار مقایسه درصدها (میله‌ای) - طراحی مدرن
    html_output += "<h2>نمودار مقایسه درصدهای دروس</h2>"
    html_output += """<div class="chart-container"><canvas id="barChart"></canvas></div>"""
    
    # آماده‌سازی داده‌های نمودار میله‌ای
    subjects = list(request.session['test_results'].keys())
    percentages = [request.session['test_results'][s]['percentage'] for s in subjects]
    
    bar_chart_data = {
        'labels': subjects,
        'datasets': [{
            'label': 'درصد',
            'data': percentages,
            'backgroundColor': ['#4361ee', '#3a36e0', '#4cc9f0', '#4caf50', '#ff9800'][:len(subjects)],
            'borderColor': ['#3a36e0', '#2d2bb6', '#45b4d6', '#429846', '#e68a00'][:len(subjects)],
            'borderWidth': 1
        }]
    }
    
    # محاسبه میانگین شاخص‌ها برای نمودار رادار و توصیه‌های فازی
    avg_indices = {
        'مدیریت ریسک': round(sum(data['risk_management'] for data in request.session['test_results'].values()) / len(request.session['test_results']), 1),
        'کارایی پاسخگویی': round(sum(data['answering_efficiency'] for data in request.session['test_results'].values()) / len(request.session['test_results']), 1),
        'بهره‌وری مطالعه': round(sum(data['study_productivity'] for data in request.session['test_results'].values()) / len(request.session['test_results']), 1),
        'اثربخشی تمرین': round(sum(data['practice_effectiveness'] for data in request.session['test_results'].values()) / len(request.session['test_results']), 1),
        'استفاده مؤثر از زمان': round(sum(data['time_utilization'] for data in request.session['test_results'].values()) / len(request.session['test_results']), 1)
    }
    
    # نرمال‌سازی شاخص‌ها برای نمودار رادار
    max_values = {
        'مدیریت ریسک': 100,       # از 0 تا 100
        'کارایی پاسخگویی': 100,   # از 0 تا 100
        'بهره‌وری مطالعه': 80,     # از 0 تا 80 (نرمال شده به 100)
        'اثربخشی تمرین': 10,      # از 0 تا 10 (نرمال شده به 100)
        'استفاده مؤثر از زمان': 30 # از 0 تا 30 (نرمال شده به 100)
    }
    
    normalized_indices = {}
    for key, value in avg_indices.items():
        if key in max_values and max_values[key] > 0:
            normalized_indices[key] = min(100, value * 100 / max_values[key])
        else:
            normalized_indices[key] = value
    
    # نمودار رادار (عنکبوتی) شاخص‌ها - طراحی مدرن
    html_output += "<h2>نمودار شاخص‌های عملکردی</h2>"
    html_output += """<div class="chart-container"><canvas id="radarChart"></canvas></div>"""
    
    # آماده‌سازی داده‌های نمودار رادار
    radar_labels = list(normalized_indices.keys())
    radar_values = [normalized_indices[label] for label in radar_labels]
    
    radar_chart_data = {
        'labels': radar_labels,
        'datasets': [
            {
                'label': 'شاخص‌های شما',
                'data': radar_values,
                'backgroundColor': 'rgba(67, 97, 238, 0.2)',
                'borderColor': 'rgba(67, 97, 238, 1)',
                'pointBackgroundColor': 'rgba(67, 97, 238, 1)',
                'pointBorderColor': '#fff',
                'pointHoverBackgroundColor': '#fff',
                'pointHoverBorderColor': 'rgba(67, 97, 238, 1)'
            },
            {
                'label': 'سطح مطلوب',
                'data': [70, 70, 70, 70, 70],  # سطح 70% برای همه شاخص‌ها
                'backgroundColor': 'rgba(244, 67, 54, 0.1)',
                'borderColor': 'rgba(244, 67, 54, 0.8)',
                'pointBackgroundColor': 'rgba(244, 67, 54, 0.8)',
                'pointBorderColor': '#fff',
                'pointHoverBackgroundColor': '#fff',
                'pointHoverBorderColor': 'rgba(244, 67, 54, 1)'
            }
        ]
    }
    
    # توصیه‌های فازی - طراحی مدرن
    html_output += "<h2>توصیه‌های کلیدی</h2>"
    
    # دریافت توصیه‌های فازی
    subjects_list = list(request.session['test_results'].keys())
    fuzzy_recommendations = get_fuzzy_combined_feedback(
        avg_indices['مدیریت ریسک'],
        avg_indices['کارایی پاسخگویی'],
        avg_indices['بهره‌وری مطالعه'],
        avg_indices['اثربخشی تمرین'],
        avg_indices['استفاده مؤثر از زمان'],
        subjects_list
    )
    
    for i, recommendation in enumerate(fuzzy_recommendations):
        html_output += f"""
        <div class="tip">
            <h3>توصیه {i+1}</h3>
            <p>{recommendation}</p>
        </div>
        """
    
    # بخش تحلیل هر درس - طراحی مدرن
    html_output += "<h2>تحلیل تفصیلی هر درس</h2>"
    
    for subject, data in request.session['test_results'].items():
        html_output += f"""
        <div class="subject-section">
            <div class="subject-header">
                <h3 class="subject-title">درس {subject}</h3>
                <div class="subject-percentage">{data['percentage']:.1f}%</div>
            </div>
            
            <table>
                <tr>
                    <th>مورد</th>
                    <th>مقدار</th>
                </tr>
                <tr>
                    <td>تعداد سوالات</td>
                    <td>{data['total']}</td>
                </tr>
                <tr>
                    <td>پاسخ صحیح</td>
                    <td>{data['correct']}</td>
                </tr>
                <tr>
                    <td>پاسخ غلط</td>
                    <td>{data['wrong']}</td>
                </tr>
                <tr>
                    <td>بی‌پاسخ</td>
                    <td>{data['blank']}</td>
                </tr>
                <tr>
                    <td>ساعات مطالعه</td>
                    <td>{data['study_hours']}</td>
                </tr>
                <tr>
                    <td>تعداد تست‌های تمرینی</td>
                    <td>{data['practice']}</td>
                </tr>
            </table>
            
            <h4>شاخص‌های عملکردی:</h4>
            <table>
                <tr>
                    <th>شاخص</th>
                    <th>مقدار</th>
                    <th>وضعیت</th>
                </tr>
                <tr>
                    <td>مدیریت ریسک</td>
                    <td>{data['risk_management']}%</td>
                    <td>{get_status_text(data['risk_management'], [50, 75, 90])}</td>
                </tr>
                <tr>
                    <td>کارایی پاسخگویی</td>
                    <td>{data['answering_efficiency']}%</td>
                    <td>{get_status_text(data['answering_efficiency'], [50, 75, 90])}</td>
                </tr>
                <tr>
                    <td>بهره‌وری مطالعه</td>
                    <td>{data['study_productivity']}</td>
                    <td>{get_status_text(data['study_productivity'], [30, 50, 70])}</td>
                </tr>
                <tr>
                    <td>اثربخشی تمرین</td>
                    <td>{data['practice_effectiveness']}</td>
                    <td>{get_status_text(data['practice_effectiveness'], [3, 6, 8])}</td>
                </tr>
                <tr>
                    <td>استفاده مؤثر از زمان</td>
                    <td>{data['time_utilization']}</td>
                    <td>{get_status_text(data['time_utilization'], [7, 15, 25])}</td>
                </tr>
            </table>
            
            <h4>توصیه‌های بهبود:</h4>
        """
        
        subject_feedback = generate_subject_feedback(subject, data)
        for feedback in subject_feedback:
            html_output += f"<div class='tip'>• {feedback}</div>"
        
        html_output += "</div>"
    
    # فوتر گزارش - طراحی مدرن
    html_output += """
    <hr style="border: 0; height: 1px; background: #e0e6ff; margin: 30px 0;">
    <p style="text-align: center; color: #666;">این گزارش توسط سیستم هوشمند تحلیل آزمون تولید شده است. © تمامی حقوق محفوظ است.</p>
    """
    
    # پایان div محتوای گزارش
    html_output += "</div>"
    
    # اسکریپت برای رسم نمودارها
    html_output += f"""
    <script>
    // تعریف داده‌های نمودار میله‌ای
    const barData = {json.dumps(bar_chart_data)};
    
    // تعریف داده‌های نمودار رادار
    const radarData = {json.dumps(radar_chart_data)};
    
    // رسم نمودار میله‌ای
    document.addEventListener('DOMContentLoaded', function() {{
        // تنظیمات فارسی برای Chart.js
        Chart.defaults.font.family = "'Tahoma', 'Arial', sans-serif";
        Chart.defaults.font.size = 14;
        
        // رسم نمودار میله‌ای
        const barCtx = document.getElementById('barChart').getContext('2d');
        new Chart(barCtx, {{
            type: 'bar',
            data: barData,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    title: {{
                        display: true,
                        text: 'مقایسه درصد دروس',
                        font: {{
                            size: 18
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'درصد'
                        }}
                    }}
                }}
            }}
        }});
        
        // رسم نمودار رادار
        const radarCtx = document.getElementById('radarChart').getContext('2d');
        new Chart(radarCtx, {{
            type: 'radar',
            data: radarData,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                elements: {{
                    line: {{
                        borderWidth: 2
                    }},
                    point: {{
                        radius: 4
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'top',
                    }},
                    title: {{
                        display: true,
                        text: 'نمودار شاخص‌های عملکردی',
                        font: {{
                            size: 18
                        }}
                    }}
                }},
                scales: {{
                    r: {{
                        angleLines: {{
                            display: true
                        }},
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            stepSize: 20
                        }}
                    }}
                }}
            }}
        }});
    }});
    </script>
    """
    
    # دکمه بازگشت - طراحی مدرن
    html_output += """
    <div class="no-print" style="margin-top: 30px; text-align: center; margin-bottom: 30px;">
        <a href="/" class="button">
            <i class="fas fa-arrow-right" style="margin-left: 8px;"></i>
            بازگشت به صفحه اصلی
        </a>
    </div>
    """
    
    html_output += "</body></html>"
    
    return HttpResponse(html_output)