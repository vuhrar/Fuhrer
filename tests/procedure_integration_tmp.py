from tempfile import TemporaryDirectory
import os

with TemporaryDirectory() as d:
    os.environ['FUHRER_DATA_DIR'] = d
    import workspace_store as w
    m = w.create_matter({'title':'اختبار مسار عمالي','matter_type':'نزاع عمالي','client_name':'العامل','opposing_party':'المنشأة','jurisdiction':'التسوية الودية','description':'نزاع حول أجر وإنهاء'})
    print('steps', len(m['procedure_steps']), [(x['step_key'], x['status']) for x in m['procedure_steps']])
    step = w.update_procedure_step(m['id'], 'amicable_settlement', {'status':'جارية','notes':'تم فتح طلب التسوية'})
    print('updated', step)
    m2 = w.get_matter(m['id'])
    print('stored', [(x['step_key'], x['status'], x['notes']) for x in m2['procedure_steps']])
    assert len(m['procedure_steps']) == 10
    assert step['status'] == 'جارية' and step['notes'] == 'تم فتح طلب التسوية'
    assert next(x for x in m2['procedure_steps'] if x['step_key']=='amicable_settlement')['status'] == 'جارية'
    print('procedure integration: PASS')
