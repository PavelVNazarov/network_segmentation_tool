# report_generator.py

def generate_report(segments, subnets, global_rules, zone_rules, equipment, validation_errors=None):
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

    report += "\nГлобальные правила взаимодействия (применяются ко всей сети):\n"
    if global_rules:
        for src, dst, svc in global_rules:
            report += f" - {src} → {dst} : {svc}\n"
    else:
        report += " - Отсутствуют.\n"

    report += "\nЗоны и специфические правила:\n"
    if zone_rules:
        for zone_name, (zone_segments, rules) in zone_rules.items():
            report += f"\nЗона: {zone_name}\n"
            report += f"Сегменты: {', '.join(zone_segments)}\n"
            report += "Правила:\n"
            for src, dst, svc in rules:
                report += f" - {src} → {dst} : {svc}\n"
    else:
        report += " - Зоны не заданы.\n"

    report += "\nСетевое оборудование:\n"
    has_eq = False
    for eq_type, count in equipment.items():
        if count > 0:
            report += f" - {eq_type}: {count} шт.\n"
            has_eq = True
    if not has_eq:
        report += " - Не указано.\n"

    return report

