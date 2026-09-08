# Google Play Publishing Checklist

## Required app assets

- App name: Cardbook
- Package name: `com.cardbook.app`
- Short description
- Full description
- App icon 512 x 512
- Feature graphic 1024 x 500
- Phone screenshots
- Privacy policy URL:
  - `https://incardbook.com/privacy/`
- Terms URL:
  - `https://incardbook.com/terms/`

## Build

- Generate AAB:

```powershell
cd mobile-cardbook
.\tool\build_release.ps1 -AppBundle
```

- Expected output:

```text
build/app/outputs/bundle/release/app-release.aab
```

## Internal testing

- Create internal test release in Google Play Console.
- Upload AAB.
- Add testers.
- Test login.
- Test company CRUD.
- Test digital card CRUD.
- Test business card CRUD.
- Test Book save/remove.
- Test alliances.
- Test profile edit/logout.
- Test update card.

## Store listing categories

- Category: Business
- Content rating: Everyone, pending questionnaire
- Ads: No, unless monetization changes later
- Data safety: use `data_safety.md` as draft

## Before production

- Confirm release signing.
- Confirm privacy policy is public.
- Confirm support contact email.
- Confirm API production URL.
- Confirm screenshots are from the native Flutter app, not WebView.
