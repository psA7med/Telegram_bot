import os
import time
import subprocess

while True:
    try:
        # إنشاء نسخة من متغيرات البيئة
        env_vars = os.environ.copy()
        
        # تشغيل البوت مع تمرير المتغيرات
        subprocess.run(
            ["python", "Botcode.py"],
            env=env_vars
        )
        time.sleep(60)  # انتظر 60 ثانية قبل إعادة التشغيل
    except Exception as e:
        print(f"حدث خطأ: {e}")
        time.sleep(10)  # انتظر 10 ثواني قبل إعادة المحاولة
