# report_generator.py

def generate_report(segments, subnets, global_rules, user_rules, segment_equipment, validation_errors=None):
    report = "=== Отчёт по сегментации локальной сети ===\n\n"

    if validation_errors:
        report += "ОБНАРУЖЕНЫ ОШИБКИ:\n"
        for err in validation_errors:
            report += f" - {err}\n"
        report += "\n"
    else:
        report += "Модель прошла валидацию успешно.\n\n"

    report += "Сегменты и подсети:\n"
    for seg in segments:
        cidr = subnets.get(seg, "не задано")
        report += f" - {seg}: {cidr}\n"

    report += "\nГлобальные правила взаимодействия:\n"
    if global_rules:
        for name, src, dst, svc in global_rules:
            report += f" - [{name}] {src} → {dst} : {svc}\n"
    else:
        report += " - Отсутствуют.\n"

    report += "\nПравила для пользователей:\n"
    if user_rules:
        for seg, fio, pos, src, dst, svc in user_rules:
            report += f" - {fio} ({pos}, сегмент {seg}): {src} → {dst} : {svc}\n"
    else:
        report += " - Не заданы.\n"

    report += "\nОборудование по сегментам:\n"
    has_eq = False
    for seg in segments:
        eq_list = segment_equipment.get(seg, {})
        if any(count > 0 for count in eq_list.values()):
            report += f"\nСегмент {seg}:\n"
            for eq, cnt in eq_list.items():
                if cnt > 0:
                    report += f"  - {eq}: {cnt} шт.\n"
                    has_eq = True
    if not has_eq:
        report += " - Не указано.\n"

    return report

