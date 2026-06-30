from companies.permissions import can_access_company, can_manage_company


def can_manage_card(user, card):
    if not user or not user.is_authenticated:
        return False
    if can_manage_company(user, card.company):
        return True
    return card.user_id == user.id and can_access_company(user, card.company)
