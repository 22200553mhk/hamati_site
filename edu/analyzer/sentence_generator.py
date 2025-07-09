import random
from collections import defaultdict

class SentenceGenerator:
    """کلاس تولید جملات متنوع برای شاخص‌های مهارتی"""
    
    def __init__(self):
        # نگهداری سابقه قالب‌های استفاده شده برای هر درس
        self.used_templates = defaultdict(lambda: defaultdict(set))
        
        # تعریف سطوح مختلف شاخص‌ها
        self.intensity_levels = {
            'very_low': (0, 30),
            'low': (30, 50),
            'medium': (50, 70),
            'high': (70, 85),
            'very_high': (85, 100)
        }
        
        # کلمات توصیفی مرتبط با هر سطح برای شاخص مدیریت ریسک
        self.risk_management_descriptors = {
            'very_low': [
                'بسیار ضعیف', 'نامناسب', 'بحرانی', 'ناکارآمد', 'نیازمند توجه فوری'
            ],
            'low': [
                'ضعیف', 'پایین', 'نیازمند تقویت جدی', 'ناکافی', 'با مشکلات اساسی'
            ],
            'medium': [
                'متوسط', 'قابل قبول', 'نسبتاً مناسب', 'در حال پیشرفت', 'با نیاز به بهبود'
            ],
            'high': [
                'خوب', 'قابل توجه', 'مناسب', 'قابل تحسین', 'مؤثر'
            ],
            'very_high': [
                'عالی', 'بسیار خوب', 'برجسته', 'چشمگیر', 'فوق‌العاده'
            ]
        }
        
        # کلمات توصیفی مرتبط با هر سطح برای شاخص بهینه‌سازی زمان
        self.time_optimization_descriptors = {
            'very_low': [
                'بسیار ضعیف', 'نامناسب', 'ناکارآمد', 'نامطلوب', 'نیازمند بازنگری اساسی'
            ],
            'low': [
                'ضعیف', 'ناکافی', 'کم‌بازده', 'نیازمند بهبود جدی', 'با کارآیی پایین'
            ],
            'medium': [
                'متوسط', 'معقول', 'قابل قبول', 'نسبتاً کارآمد', 'در حال پیشرفت'
            ],
            'high': [
                'خوب', 'مؤثر', 'کارآمد', 'مناسب', 'موفق'
            ],
            'very_high': [
                'عالی', 'بسیار مؤثر', 'بهینه', 'بسیار کارآمد', 'فوق‌العاده'
            ]
        }
        
        # افعال مناسب برای هر سطح
        self.verbs = {
            'very_low': [
                'نیاز به بازنگری اساسی دارد', 'باید به طور جدی تقویت شود', 'دچار مشکلات اساسی است'
            ],
            'low': [
                'نیاز به بهبود دارد', 'باید تقویت شود', 'چندان مناسب نیست'
            ],
            'medium': [
                'در حال پیشرفت است', 'می‌تواند بهتر شود', 'نسبتاً مناسب است'
            ],
            'high': [
                'در سطح خوبی قرار دارد', 'قابل تحسین است', 'نشان‌دهنده تلاش شماست'
            ],
            'very_high': [
                'در سطح بسیار بالایی قرار دارد', 'نشان‌دهنده مهارت بالای شماست', 'یکی از نقاط قوت شماست'
            ]
        }
        
        # پیشنهادات برای هر سطح
        self.suggestions = {
            'very_low': [
                'پیشنهاد می‌شود روی این مهارت به صورت ویژه کار کنید',
                'توصیه می‌شود از روش‌های آموزشی برای تقویت این مهارت استفاده کنید',
                'لازم است توجه ویژه‌ای به این مهارت داشته باشید',
                'بهبود این مهارت می‌تواند تأثیر قابل توجهی در نتیجه آزمون شما داشته باشد',
                'تمرین‌های هدفمند می‌تواند به بهبود این مهارت کمک کند'
            ],
            'low': [
                'با تمرین بیشتر می‌توانید این مهارت را بهبود دهید',
                'توصیه می‌شود بر روی تقویت این مهارت تمرکز کنید',
                'این مهارت نیاز به توجه بیشتری دارد',
                'با راهکارهای مناسب می‌توانید این مهارت را تقویت کنید',
                'بهبود این مهارت می‌تواند نتایج شما را ارتقا دهد'
            ],
            'medium': [
                'با کمی تلاش بیشتر می‌توانید این مهارت را به سطح بالاتری برسانید',
                'پیشرفت خوبی داشته‌اید، اما هنوز جای پیشرفت وجود دارد',
                'توصیه می‌شود به تقویت این مهارت ادامه دهید',
                'با تداوم تمرین می‌توانید به نتایج بهتری دست یابید',
                'روند پیشرفت شما مثبت است، آن را ادامه دهید'
            ],
            'high': [
                'تلاش شما در این زمینه نتیجه داده است، آن را حفظ کنید',
                'این مهارت یکی از نقاط قوت شماست',
                'عملکرد خوبی در این زمینه دارید',
                'این سطح از مهارت می‌تواند به موفقیت شما کمک کند',
                'با حفظ این سطح از مهارت، می‌توانید موفقیت‌های بیشتری کسب کنید'
            ],
            'very_high': [
                'عملکرد عالی شما در این زمینه، یک مزیت رقابتی محسوب می‌شود',
                'این مهارت یکی از نقاط قوت برجسته شماست',
                'تسلط شما در این زمینه می‌تواند الگویی برای دیگران باشد',
                'این سطح از مهارت می‌تواند به موفقیت‌های چشمگیری منجر شود',
                'با حفظ این سطح عالی، نتایج درخشانی کسب خواهید کرد'
            ]
        }
        
        # قالب‌های جمله برای شاخص مدیریت ریسک
        self.risk_management_templates = [
            "مهارت {descriptor} شما در مدیریت ریسک {subject} {verb}. {suggestion}",
            "در زمینه مدیریت ریسک {subject}، عملکرد شما {descriptor} {verb}. {suggestion}",
            "توانایی شما در تشخیص سوالاتی که باید جواب دهید در درس {subject} {descriptor} {verb}. {suggestion}",
            "مدیریت ریسک {descriptor} شما در {subject} نشان می‌دهد که {verb}. {suggestion}",
            "شاخص مدیریت ریسک شما در درس {subject} با امتیاز {score}%، در سطح {descriptor} قرار دارد. {suggestion}",
            "در انتخاب سوالات مناسب برای پاسخگویی در {subject}، مهارت شما {descriptor} {verb}. {suggestion}",
            "عملکرد {descriptor} شما در عدم پاسخ به سوالات نامطمئن در {subject} {verb}. {suggestion}"
        ]
        
        # قالب‌های جمله برای شاخص بهینه‌سازی زمان
        self.time_optimization_templates = [
            "مهارت {descriptor} شما در بهینه‌سازی زمان {subject} {verb}. {suggestion}",
            "در زمینه استفاده بهینه از زمان در {subject}، عملکرد شما {descriptor} {verb}. {suggestion}",
            "توانایی شما در تخصیص زمان مناسب به هر سوال در درس {subject} {descriptor} {verb}. {suggestion}",
            "بهینه‌سازی زمان {descriptor} شما در {subject} نشان می‌دهد که {verb}. {suggestion}",
            "شاخص بهینه‌سازی زمان شما در درس {subject} با امتیاز {score}%، در سطح {descriptor} قرار دارد. {suggestion}",
            "در مدیریت زمان و تمرکز بر سوالات مناسب در {subject}، مهارت شما {descriptor} {verb}. {suggestion}",
            "عملکرد {descriptor} شما در استفاده مؤثر از زمان آزمون در {subject} {verb}. {suggestion}"
        ]
    
    def _get_intensity_level(self, score):
        """تعیین سطح شدت بر اساس امتیاز"""
        for level, (min_val, max_val) in self.intensity_levels.items():
            if min_val <= score < max_val:
                return level
        return 'very_high'  # برای امتیاز 100
    
    def _select_template(self, templates, subject, indicator):
        """انتخاب قالب جمله غیرتکراری"""
        # فیلتر کردن قالب‌های استفاده نشده
        used = self.used_templates[subject][indicator]
        unused_templates = [i for i, t in enumerate(templates) if i not in used]
        
        # اگر همه قالب‌ها استفاده شده‌اند، دوباره همه را در دسترس قرار بده
        if not unused_templates:
            unused_templates = list(range(len(templates)))
            self.used_templates[subject][indicator] = set()
        
        # انتخاب تصادفی یک قالب
        template_index = random.choice(unused_templates)
        template = templates[template_index]
        
        # ثبت قالب استفاده شده
        self.used_templates[subject][indicator].add(template_index)
        
        return template
    
    def generate_risk_management_feedback(self, subject, score):
        """تولید بازخورد برای مدیریت ریسک"""
        level = self._get_intensity_level(score)
        template = self._select_template(self.risk_management_templates, subject, 'risk_management')
        
        descriptor = random.choice(self.risk_management_descriptors[level])
        verb = random.choice(self.verbs[level])
        suggestion = random.choice(self.suggestions[level])
        
        feedback = template.format(
            subject=subject,
            descriptor=descriptor,
            verb=verb,
            suggestion=suggestion,
            score=round(score, 1)
        )
        
        return feedback
    
    def generate_time_optimization_feedback(self, subject, score):
        """تولید بازخورد برای بهینه‌سازی زمان"""
        level = self._get_intensity_level(score)
        template = self._select_template(self.time_optimization_templates, subject, 'time_optimization')
        
        descriptor = random.choice(self.time_optimization_descriptors[level])
        verb = random.choice(self.verbs[level])
        suggestion = random.choice(self.suggestions[level])
        
        feedback = template.format(
            subject=subject,
            descriptor=descriptor,
            verb=verb,
            suggestion=suggestion,
            score=round(score, 1)
        )
        
        return feedback


# مثال استفاده:
if __name__ == "__main__":
    generator = SentenceGenerator()
    
    # شبیه‌سازی چند دور استفاده برای یک درس
    subject = "ریاضیات"
    risk_management_score = 65.5  # امتیاز متوسط
    time_optimization_score = 82.3  # امتیاز بالا
    
    print("بازخورد مدیریت ریسک:")
    for _ in range(5):  # تولید 5 بازخورد مختلف
        feedback = generator.generate_risk_management_feedback(subject, risk_management_score)
        print(f"- {feedback}")
    
    print("\nبازخورد بهینه‌سازی زمان:")
    for _ in range(5):  # تولید 5 بازخورد مختلف
        feedback = generator.generate_time_optimization_feedback(subject, time_optimization_score)
        print(f"- {feedback}")