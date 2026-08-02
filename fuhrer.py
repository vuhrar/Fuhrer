# fuhrer.py - CLI entrypoint for Führar
import os
import sys
from dotenv import load_dotenv
load_dotenv()

import click
import ai_engine
import file_processing
import api


@click.group()
def cli():
    """Führar CLI - تشغيل محلي لتطبيق التحليل القانوني"""
    pass


@cli.command()
@click.argument('paths', nargs=-1, type=click.Path(exists=True))
@click.option('--analyze', '-a', is_flag=True, help='بعد المعالجة، استدعاء النموذج لتحليل الملفات المجمعة')
@click.option('--preset', default=None, help='اسم النموذج (اختياري)')
@click.option('--api-key', default=None, help='مفتاح API لاستخدامه (اختياري)')
def process(paths, analyze, preset, api_key):
    """معالجة ملفات متعددة (PDF/DOCX/TXT/JSON/CSV/صور)"""
    if not paths:
        click.echo("لم تُمرّر أي ملفات للمعالجة.")
        sys.exit(1)

    files = []
    # فتح الملفات بوضع الباينري وتمريرها لوظائف المعالجة
    for p in paths:
        f = open(p, 'rb')
        # object متوافق مع واجهة extract_text_from_file
        files.append(f)

    batch = file_processing.process_multiple_files(files)

    click.echo(f"تمت معالجة {batch['total']} ملف — ناجح: {batch['success']}، فاشل: {batch['failed']}")

    for r in batch['results']:
        status = '✅' if r['success'] else '❌'
        click.echo(f"{status} {r['filename']} — صفحات: {r.get('pages', 0)} — أحرف: {len(r.get('text',''))}")

    if analyze and batch['success'] > 0:
        docs_text = batch['texts']
        prompt = '\n\n---\n'.join(docs_text)
        preset_name = preset or os.environ.get('PRESET_NAME', 'Führer Law Brain (Qwen 0.6B) 🧠')
        api_key_final = api_key or os.environ.get('API_KEY', '')
        click.echo('جاري استدعاء نموذج الذكاء الاصطناعي...')
        resp = ai_engine.call_ai(prompt=prompt, history=[], system='', preset_name=preset_name, api_key=api_key_final)
        click.echo('\n=== استجابة النموذج ===\n')
        click.echo(resp)

    for f in files:
        try:
            f.close()
        except:
            pass


@cli.command()
@click.argument('prompt', nargs=-1)
@click.option('--preset', default=None, help='اسم النموذج (اختياري)')
@click.option('--api-key', default=None, help='مفتاح API لاستخدامه (اختياري)')
def analyze(prompt, preset, api_key):
    """استدعاء النموذج لتحليل نص/سؤال محدد"""
    text = ' '.join(prompt).strip()
    if not text:
        click.echo('أدخل نصًا أو سؤالاً للتحليل.')
        sys.exit(1)
    preset_name = preset or os.environ.get('PRESET_NAME', 'Führer Law Brain (Qwen 0.6B) 🧠')
    api_key_final = api_key or os.environ.get('API_KEY', '')
    click.echo(f"استدعاء النموذج {preset_name} ...")
    resp = ai_engine.call_ai(prompt=text, history=[], system='', preset_name=preset_name, api_key=api_key_final)
    click.echo('\n=== استجابة النموذج ===\n')
    click.echo(resp)


@cli.command('list-models')
def list_models():
    """عرض أسماء النماذج المتاحة"""
    for name in ai_engine.preset_names():
        click.echo(name)


@cli.command('test-conn')
@click.option('--preset', default=None, help='اسم النموذج لاختباره')
@click.option('--api-key', default=None, help='مفتاح API لاستخدامه (اختياري)')
def test_conn(preset, api_key):
    """اختبار الاتصال بنموذج محدد"""
    preset_name = preset or os.environ.get('PRESET_NAME', 'Führer Law Brain (Qwen 0.6B) 🧠')
    api_key_final = api_key or os.environ.get('API_KEY', '')
    ok, msg = ai_engine.test_connection(preset_name, api_key_final)
    click.echo(msg)


if __name__ == '__main__':
    cli()
