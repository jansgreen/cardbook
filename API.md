# Cardbook API

Base URL: `/api/v1/`

Protected endpoints use JWT:

```http
Authorization: Bearer <access_token>
```

## Response Format

Success:

```json
{
  "success": true,
  "message": "Operation successful.",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Error description.",
  "errors": {}
}
```

## Health Check

```http
GET /
```

Returns the API status and the main endpoint groups.

## Accounts

```http
POST /api/v1/accounts/register/
POST /api/v1/accounts/login/
POST /api/v1/accounts/token/refresh/
POST /api/v1/accounts/token/verify/
POST /api/v1/accounts/logout/
GET /api/v1/accounts/me/
GET /api/v1/accounts/profile/
PATCH /api/v1/accounts/profile/
```

Register:

```json
{
  "username": "demo",
  "email": "demo@example.com",
  "password": "StrongPassword123!",
  "password_confirm": "StrongPassword123!",
  "preferred_language": "es"
}
```

Register response includes:

```json
{
  "success": true,
  "message": "User registered successfully.",
  "data": {
    "user": {},
    "tokens": {
      "refresh": "...",
      "access": "..."
    },
    "access": "...",
    "refresh": "..."
  }
}
```

Login:

```json
{
  "username": "demo",
  "password": "StrongPassword123!"
}
```

Login response:

```json
{
  "success": true,
  "message": "Login successful.",
  "data": {
    "user": {},
    "tokens": {
      "refresh": "...",
      "access": "..."
    }
  }
}
```

Refresh token:

```http
POST /api/v1/accounts/token/refresh/
```

```json
{
  "refresh": "..."
}
```

Current user:

```http
GET /api/v1/accounts/me/
```

## Companies

```http
GET /api/v1/companies/
POST /api/v1/companies/
GET /api/v1/companies/{id}/
PATCH /api/v1/companies/{id}/
DELETE /api/v1/companies/{id}/
```

Create company:

```json
{
  "name": "Cardbook Coffee",
  "phone_number": "+18095550100",
  "email": "hello@cardbook.test",
  "website": "https://cardbook.test",
  "description": "Digital cards for local businesses."
}
```

`DELETE` performs a soft delete by setting `is_active=false`.

## Mobile Bootstrap

Flutter should start with these endpoints:

```http
GET /api/v1/mobile/config/
GET /api/v1/mobile/bootstrap/
GET /api/v1/mobile/dashboard/
GET /api/v1/mobile/companies/
GET /api/v1/mobile/cards/
GET /api/v1/mobile/book/
GET /api/v1/mobile/jobs/
GET /api/v1/mobile/websites/
GET /api/v1/mobile/actions/
```

`/api/v1/mobile/config/` is public and returns API URLs, media base URL, Android version URL, and download URL.

`/api/v1/mobile/bootstrap/` requires JWT and returns the current user, mobile endpoint map, CRUD links, navigation entries, and capabilities such as whether the user can create cards, manage websites, publish websites, or create a White Card Job.

`/api/v1/mobile/dashboard/` requires JWT and returns a compact home payload:

```json
{
  "success": true,
  "message": "Mobile dashboard retrieved successfully.",
  "data": {
    "user": {},
    "summary": {
      "companies": 0,
      "digital_cards": 0,
      "business_cards": 0,
      "book_items": 0,
      "posts": 0,
      "alliances": 0,
      "pending_alliances": 0,
      "views": 0,
      "clicks": 0,
      "excellent": 0,
      "notifications": 0
    },
    "companies": [],
    "digital_cards": [],
    "business_cards": [],
    "recent_posts": [],
    "suggested_companies": [],
    "quick_links": {}
  }
}
```

Mobile screen endpoints:

- `/api/v1/mobile/companies/`: paginated companies available to the current user.
- `/api/v1/mobile/cards/`: digital profiles and business presentation cards, including `public_url` and `qr_svg_url`.
- `/api/v1/mobile/book/`: saved businesses, saved hiring candidates, and job recommendations.
- `/api/v1/mobile/jobs/`: current user's White Card Job, available public jobs, and company recommendations.
- `/api/v1/mobile/websites/`: websites available to the user, including `public_url` and `publish_status`.
- `/api/v1/mobile/actions/`: native action metadata for phone, email, WhatsApp, maps, share, contact download, and QR download.

Recommended Flutter boot flow:

1. `GET /api/v1/mobile/config/`.
2. If no stored token, show login/register.
3. `POST /api/v1/accounts/login/`.
4. Store `data.tokens.access` and `data.tokens.refresh` in secure storage.
5. `GET /api/v1/accounts/me/`.
6. `GET /api/v1/mobile/bootstrap/`.
7. `GET /api/v1/mobile/dashboard/`.
8. Load screen-specific endpoints as the user navigates.
9. On `401`, call `/api/v1/accounts/token/refresh/` and retry once.

## Public Marketplace

```http
GET /api/v1/marketplace/
GET /api/v1/marketplace/?q=software&limit=12
```

Public endpoint. It returns marketplace-ready results for business presentation cards, White Card Jobs, and published websites.

```json
{
  "success": true,
  "message": "Marketplace retrieved successfully.",
  "data": {
    "summary": {
      "business_cards": 27,
      "white_card_jobs": 10,
      "websites": 5
    },
    "business_cards": [],
    "white_card_jobs": [],
    "websites": []
  }
}
```

Each item includes `type`, `title`, `subtitle`, `company`, `category`, `city`, `region`, `logo`, `photo`, `public_url`, and `qr_svg_url` when applicable.

## Members

```http
GET /api/v1/companies/{company_id}/members/
POST /api/v1/companies/{company_id}/members/
PATCH /api/v1/companies/{company_id}/members/{member_id}/
DELETE /api/v1/companies/{company_id}/members/{member_id}/
```

Roles: `owner`, `admin`, `manager`, `staff`.

Create member:

```json
{
  "user": 2,
  "role": "staff"
}
```

Only `owner` and `admin` can add, edit, or delete members.

## Cards

```http
GET /api/v1/cards/
POST /api/v1/cards/
GET /api/v1/cards/{slug}/
PATCH /api/v1/cards/{id}/
DELETE /api/v1/cards/{id}/
```

Create card:

```json
{
  "company": 1,
  "job_title": "Founder",
  "phone_number": "+18095550100",
  "email": "demo@cardbook.test",
  "website": "https://cardbook.test/demo"
}
```

Public card lookup with language fallback:

```http
GET /api/v1/cards/{slug}/?lang=en
```

If the requested language does not exist, the API returns Spanish (`es`) when available.

## Translations

```http
GET /api/v1/cards/{card_id}/translations/
POST /api/v1/cards/{card_id}/translations/
```

Supported languages: `es`, `en`, `fr`, `pt`.

Create translation:

```json
{
  "language": "es",
  "full_name": "Demo User",
  "bio": "Especialista en tarjetas digitales.",
  "services": "Diseño, QR, perfiles digitales",
  "address": "Santo Domingo",
  "custom_message": "Conecta conmigo."
}
```

## Analytics

```http
POST /api/v1/analytics/cards/{card_id}/view/
POST /api/v1/analytics/cards/{card_id}/click/
GET /api/v1/analytics/cards/{card_id}/stats/
```

Register view:

```json
{
  "source": "qr",
  "language": "es"
}
```

Register click:

```json
{
  "click_type": "website"
}
```

Click types: `phone`, `email`, `website`, `whatsapp`, `social`.

Stats require authentication and card permissions.

## Website Builder

Dashboard route:

```http
GET /dashboard/companies/{company_id}/website/
```

Public site routes:

```http
GET /site/{website_slug}/
GET /site/{website_slug}/{page_slug}/
GET /site/{website_slug}/?lang=en
```

REST endpoints:

```http
GET|POST /api/v1/websites/
GET|PATCH|DELETE /api/v1/websites/{id}/
GET|POST /api/v1/pages/
GET|PATCH|DELETE /api/v1/pages/{id}/
GET|POST /api/v1/layouts/
GET|PATCH|DELETE /api/v1/layouts/{id}/
GET|POST /api/v1/sections/
GET|PATCH|DELETE /api/v1/sections/{id}/
GET|POST /api/v1/components/
GET|PATCH|DELETE /api/v1/components/{id}/
GET|POST /api/v1/blocks/
GET|PATCH|DELETE /api/v1/blocks/{id}/
GET /api/v1/themes/
GET /api/v1/public-sites/{website_slug}/
GET /api/v1/public-sites/{website_slug}/{page_slug}/
```

Translation endpoints:

```http
GET|POST /api/v1/page-translations/
GET|PATCH|DELETE /api/v1/page-translations/{id}/
GET|POST /api/v1/section-translations/
GET|PATCH|DELETE /api/v1/section-translations/{id}/
GET|POST /api/v1/component-translations/
GET|PATCH|DELETE /api/v1/component-translations/{id}/
GET|POST /api/v1/block-translations/
GET|PATCH|DELETE /api/v1/block-translations/{id}/
```

Private builder endpoints require `Authorization: Bearer <access>` and company management permission. Public site endpoints do not require authentication.

## Referral & Agent System

Agent endpoints:

```http
POST /api/v1/referrals/agent/invite/
GET /api/v1/referrals/agent/me/
GET /api/v1/referrals/agent/link/
```

Register source and referrals:

```http
POST /api/v1/referrals/register-source/
GET /api/v1/referrals/my-referrals/
```

`register-source` accepts:

```json
{
  "referral_code": "AGT-8F92KD",
  "source_url": "https://cardbook.com/register/?ref=AGT-8F92KD"
}
```

Commissions:

```http
GET /api/v1/referrals/commissions/
GET /api/v1/referrals/commissions/{id}/
POST /api/v1/referrals/commissions/generate/
POST /api/v1/referrals/commissions/{id}/approve/
POST /api/v1/referrals/commissions/{id}/mark-paid/
```

Generate commission accepts:

```json
{
  "company_id": 1,
  "plan_name": "Plan Pro",
  "payment_amount": "49.99",
  "currency": "USD",
  "payment_reference": "stripe-payment-id"
}
```

Admin endpoints:

```http
GET /api/v1/referrals/admin/agents/
GET /api/v1/referrals/admin/referrals/
GET /api/v1/referrals/admin/commissions/
GET /api/v1/referrals/admin/reports/referrals.csv
```

Web dashboard:

```http
GET /dashboard/referrals/
```

Registration also accepts referral codes through:

```http
GET /register/?ref=AGT-8F92KD
POST /api/v1/accounts/register/?ref=AGT-8F92KD
```

## Android Smoke Test Flow

1. `POST /api/v1/accounts/register/` and store `data.tokens.access` and `data.tokens.refresh`.
2. Add `Authorization: Bearer <access>` to protected requests.
3. `POST /api/v1/companies/` to create a company.
4. `POST /api/v1/cards/` using the returned company `id`.
5. `POST /api/v1/cards/{card_id}/translations/` with `language=es`.
6. Remove the auth header and call `GET /api/v1/cards/{slug}/?lang=en` to test public fallback.
7. `POST /api/v1/analytics/cards/{card_id}/view/` when the card is opened.
8. `POST /api/v1/analytics/cards/{card_id}/click/` when a user taps a contact action.
9. Add auth again and call `GET /api/v1/analytics/cards/{card_id}/stats/`.

## Android Notes

1. Store tokens securely.
2. Send the access token as `Authorization: Bearer <token>`.
3. Send image uploads as `multipart/form-data`.
4. Refresh login when the access token expires.
5. Use `success`, `message`, and `errors` to drive UI feedback.

## Permission Rules

Companies:

- `owner` and `admin` can update company data.
- `owner` and `admin` can add, update, or remove members.
- `manager` and `staff` can read company data if they belong to the company.
- Users outside the company receive `404` for private company resources.
- Company deletion is soft delete only.

Memberships:

- A company creator automatically receives an `owner` membership.
- Only the company owner can assign the `owner` role.
- Admins cannot edit or delete an owner membership.
- A membership user cannot be changed after creation.
- Duplicate company memberships are rejected.

Cards:

- Public card detail by `slug` does not require authentication.
- Creating cards requires company membership.
- `owner` and `admin` can edit cards in their company.
- `staff` can edit only their own card if they belong to that company.
- Cards are soft deleted with `is_active=false`.

Analytics:

- Views and clicks are public write endpoints.
- Stats require authentication and card management permission.
