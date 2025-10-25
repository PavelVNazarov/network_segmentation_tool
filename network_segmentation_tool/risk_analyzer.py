# risk_analyzer.py

def analyze_risks(segments, global_rules, user_rules, segment_equipment):
    """
    Анализирует модель на наличие потенциальных рисков и сложностей.
    Возвращает список предупреждений.
    """
    warnings = []

    # 1. Открытые сервисы (особенно опасные)
    dangerous_ports = {"SSH": 22, "RDP": 3389, "SMB": 445}
    for name, src, dst, svc in global_rules:
        if svc in dangerous_ports:
            warnings.append(
                f" Глобальное правило '{name}': открыт опасный сервис {svc} ({dangerous_ports[svc]}) между {src} и {dst}")

    for seg, fio, pos, target, svc in user_rules:
        if svc in dangerous_ports:
            warnings.append(f" Пользователь '{fio}' имеет доступ к опасному сервису {svc} в сегменте {target}")

    # 2. Доступ из Guest-сегмента
    guest_segment = None
    for seg in segments:
        if "guest" in seg.lower():
            guest_segment = seg
            break

    if guest_segment:
        for name, src, dst, svc in global_rules:
            if src == guest_segment:
                warnings.append(f"️ Глобальный доступ из ненадёжного сегмента '{guest_segment}' к {dst} по {svc}")
        for seg, fio, pos, target, svc in user_rules:
            if seg == guest_segment:
                warnings.append(f"⚠ Пользователь из '{guest_segment}' имеет доступ к {target} по {svc}")

    # 3. Отсутствие оборудования в сегменте
    for seg in segments:
        eq_dict = segment_equipment.get(seg, {})
        total_eq = sum(eq_dict.values())
        if total_eq == 0:
            warnings.append(f" Сегмент '{seg}' не содержит оборудования (возможно, ошибка)")

    # 4. Избыточные правила (например, полный доступ между сегментами)
    # Простой пример: если между двумя сегментами >3 разных сервисов
    from collections import defaultdict
    inter_seg_services = defaultdict(set)
    for _, src, dst, svc in global_rules:
        if src != dst:
            inter_seg_services[(src, dst)].add(svc)

    for (src, dst), services in inter_seg_services.items():
        if len(services) > 3:
            warnings.append(f" Между {src} и {dst} разрешено {len(services)} сервисов — возможно, избыточно")

    return warnings if warnings else ["Модель не содержит явных рисков."]