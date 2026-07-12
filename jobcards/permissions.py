from companies.permissions import can_access_company, can_manage_company


def can_save_candidate(user, company):
    return user.is_authenticated and can_access_company(user, company)


def can_manage_candidate_save(user, saved_job_card):
    return user.is_authenticated and can_manage_company(user, saved_job_card.company)
