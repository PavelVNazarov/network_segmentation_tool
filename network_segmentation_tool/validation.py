# validation.py
import ipaddress


def validate_subnets(subnets):
    errors = []
    net_objects = []
    for name, cidr in subnets.items():
        if not cidr:
            continue
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            net_objects.append((name, net))
        except ValueError:
            errors.append(f"Некорректный CIDR для сегмента '{name}': {cidr}")

    for i in range(len(net_objects)):
        for j in range(i + 1, len(net_objects)):
            if net_objects[i][1].overlaps(net_objects[j][1]):
                errors.append(f"Пересечение подсетей: '{net_objects[i][0]}' и '{net_objects[j][0]}'")

    return errors


def validate_rules(rules, all_segments):
    errors = []
    seen = set()
    for rule_name, src, dst, svc in rules:
        if src not in all_segments or dst not in all_segments:
            errors.append(f"Неизвестный сегмент в правиле '{rule_name}': {src} → {dst}")
            continue
        key = (src, dst, svc)
        if key in seen:
            errors.append(f"Дублирующее правило: {src} → {dst} по {svc} (уже задано ранее)")
        else:
            seen.add(key)
    return errors


def validate_user_rules(user_rules, all_segments):
    errors = []
    seen = set()  # Теперь ключ включает сегмент источника
    for seg, fio, pos, target_seg, svc in user_rules:
        if seg not in all_segments:
            errors.append(f"Пользователь '{fio}': сегмент источника '{seg}' не объявлен")
        if target_seg not in all_segments:
            errors.append(f"Пользователь '{fio}': недопустимый целевой сегмент '{target_seg}'")

        # Ключ для дубликата: (сегмент_источника, ФИО, целевой_сегмент, сервис)
        user_key = (seg, fio, target_seg, svc)
        if user_key in seen:
            errors.append(
                f"Дублирующее правило для пользователя '{fio}' в сегменте {seg}: доступ к {target_seg} по {svc}")
        else:
            seen.add(user_key)
    return errors

