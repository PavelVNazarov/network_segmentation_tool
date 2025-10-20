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

    # Проверка пересечений
    for i in range(len(net_objects)):
        for j in range(i + 1, len(net_objects)):
            if net_objects[i][1].overlaps(net_objects[j][1]):
                errors.append(f"Пересечение подсетей: '{net_objects[i][0]}' и '{net_objects[j][0]}'")

    return errors if errors else None

def validate_rules(rules, all_segments):
    errors = []
    seen = set()
    for rule_name, src, dst, svc in rules:
        if src not in all_segments or dst not in all_segments:
            errors.append(f"Неизвестный сегмент в правиле '{rule_name}': {src} → {dst}")
            continue
        key = (src, dst, svc)
        if key in seen:
            errors.append(f"Дублирующее правило в '{rule_name}': {src} → {dst} по {svc}")
        seen.add(key)
    return errors if errors else None

def validate_user_rules(user_rules, all_segments):
    errors = []
    for rule in user_rules:
        seg, fio, pos, src, dst, svc = rule
        if seg not in all_segments:
            errors.append(f"Пользователь '{fio}': сегмент '{seg}' не объявлен")
        if src not in all_segments or dst not in all_segments:
            errors.append(f"Пользователь '{fio}': недопустимое взаимодействие {src} → {dst}")
    return errors if errors else None

