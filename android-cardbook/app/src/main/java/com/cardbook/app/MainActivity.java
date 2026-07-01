package com.cardbook.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.provider.Settings;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.JavascriptInterface;
import android.webkit.MimeTypeMap;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int FILE_CHOOSER_REQUEST = 4927;
    private static final int BLUE = Color.rgb(0, 87, 184);
    private static final int BLUE_DARK = Color.rgb(0, 56, 117);
    private static final int GOLD = Color.rgb(216, 164, 65);
    private static final int INK = Color.rgb(5, 22, 48);
    private static final int WHITE = Color.WHITE;
    private static final String BASE_URL = "https://cardbook-45cf0409dc07.herokuapp.com/";
    private static final String BASE_HOST = "cardbook-45cf0409dc07.herokuapp.com";
    private static final String VERSION_URL = BASE_URL + "android/version/";

    private FrameLayout container;
    private WebView webView;
    private ProgressBar progressBar;
    private TextView titleView;
    private View splashView;
    private ValueCallback<Uri[]> fileUploadCallback;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        renderShell();
        if (savedInstanceState == null) {
            webView.loadUrl(BASE_URL);
            checkForUpdates();
        } else {
            webView.restoreState(savedInstanceState);
            hideSplash();
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        if (splashView != null && splashView.getVisibility() == View.VISIBLE) {
            hideSplash();
            return;
        }
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }
        super.onBackPressed();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != FILE_CHOOSER_REQUEST || fileUploadCallback == null) {
            return;
        }

        Uri[] result = null;
        if (resultCode == RESULT_OK && data != null) {
            if (data.getClipData() != null) {
                int count = data.getClipData().getItemCount();
                result = new Uri[count];
                for (int i = 0; i < count; i++) {
                    result[i] = data.getClipData().getItemAt(i).getUri();
                }
            } else if (data.getData() != null) {
                result = new Uri[]{data.getData()};
            }
        }
        fileUploadCallback.onReceiveValue(result);
        fileUploadCallback = null;
    }

    private void renderShell() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(244, 246, 249));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setProgress(0);
        progressBar.setVisibility(View.GONE);

        container = new FrameLayout(this);
        webView = new WebView(this);
        configureWebView();
        container.addView(webView, new FrameLayout.LayoutParams(-1, -1));

        splashView = createSplashView();
        container.addView(splashView, new FrameLayout.LayoutParams(-1, -1));

        root.addView(progressBar, new LinearLayout.LayoutParams(-1, dp(3)));
        root.addView(container, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
    }

    private View createSplashView() {
        LinearLayout splash = new LinearLayout(this);
        splash.setOrientation(LinearLayout.VERTICAL);
        splash.setGravity(Gravity.CENTER);
        splash.setPadding(dp(32), dp(32), dp(32), dp(32));
        splash.setBackground(gradient(BLUE_DARK, BLUE));

        ImageView logo = new ImageView(this);
        logo.setImageResource(getResources().getIdentifier("cardbook_logo", "drawable", getPackageName()));
        splash.addView(logo, new LinearLayout.LayoutParams(dp(108), dp(108)));

        TextView name = new TextView(this);
        name.setText("Cardbook");
        name.setTextColor(WHITE);
        name.setTextSize(34);
        name.setTypeface(Typeface.DEFAULT_BOLD);
        name.setGravity(Gravity.CENTER);
        name.setPadding(0, dp(18), 0, dp(6));
        splash.addView(name, new LinearLayout.LayoutParams(-1, -2));

        TextView tagline = new TextView(this);
        tagline.setText("Tarjetas digitales inteligentes");
        tagline.setTextColor(Color.argb(220, 255, 255, 255));
        tagline.setTextSize(15);
        tagline.setGravity(Gravity.CENTER);
        splash.addView(tagline, new LinearLayout.LayoutParams(-1, -2));

        ProgressBar spinner = new ProgressBar(this);
        LinearLayout.LayoutParams spinnerParams = new LinearLayout.LayoutParams(dp(42), dp(42));
        spinnerParams.setMargins(0, dp(26), 0, 0);
        splash.addView(spinner, spinnerParams);
        return splash;
    }

    private void configureWebView() {
        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, true);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        webView.addJavascriptInterface(new AndroidBridge(), "CardbookAndroid");

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                progressBar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
                progressBar.setProgress(newProgress);
                super.onProgressChanged(view, newProgress);
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                titleView.setText("Cardbook");
                super.onReceivedTitle(view, title);
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {
                if (fileUploadCallback != null) {
                    fileUploadCallback.onReceiveValue(null);
                }
                fileUploadCallback = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                try {
                    startActivityForResult(intent, FILE_CHOOSER_REQUEST);
                } catch (Exception error) {
                    fileUploadCallback = null;
                    Toast.makeText(MainActivity.this, "No se pudo abrir el selector de archivos", Toast.LENGTH_SHORT).show();
                    return false;
                }
                return true;
            }
        });

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleUrl(request.getUrl().toString());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleUrl(url);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                hideSplash();
                injectAndroidHelpers(view);
                super.onPageFinished(view, url);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request != null && request.isForMainFrame()) {
                    showOfflineScreen();
                }
                super.onReceivedError(view, request, error);
            }

            @Override
            public void onReceivedHttpError(WebView view, WebResourceRequest request, WebResourceResponse errorResponse) {
                if (request != null && request.isForMainFrame() && errorResponse != null && errorResponse.getStatusCode() >= 500) {
                    showOfflineScreen();
                }
                super.onReceivedHttpError(view, request, errorResponse);
            }
        });

        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {
                downloadFile(url, mimetype);
            }
        });
    }

    private boolean handleUrl(String url) {
        if (url == null) return false;
        Uri uri = Uri.parse(url);
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase(Locale.US);
        String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase(Locale.US);

        if (isInternalHost(host) && ("https".equals(scheme) || "http".equals(scheme))) {
            return false;
        }

        if ("tel".equals(scheme) || "mailto".equals(scheme) || "sms".equals(scheme) || "geo".equals(scheme)) {
            openExternal(url);
            return true;
        }

        if ("whatsapp".equals(scheme) || "intent".equals(scheme)) {
            openExternal(url);
            return true;
        }

        if ("http".equals(scheme) || "https".equals(scheme)) {
            openExternal(url);
            return true;
        }

        Toast.makeText(this, "Enlace no permitido en Cardbook", Toast.LENGTH_SHORT).show();
        return true;
    }

    private boolean isInternalHost(String host) {
        return BASE_HOST.equals(host);
    }

    private void injectAndroidHelpers(WebView view) {
        String js =
            "(function(){"
                + "if(window.__cardbookAndroidReady){return;}"
                + "window.__cardbookAndroidReady=true;"
                + "if(window.CardbookAndroid){"
                + "window.CardbookNativeShare=function(title,text,url){window.CardbookAndroid.share(title||document.title,text||'',url||location.href);};"
                + "if(!navigator.share){navigator.share=function(data){window.CardbookAndroid.share((data&&data.title)||document.title,(data&&data.text)||'',(data&&data.url)||location.href);return Promise.resolve();};}"
                + "}"
            + "})();";
        view.evaluateJavascript(js, null);
    }

    private void checkForUpdates() {
        if (!isNetworkAvailable()) {
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                HttpURLConnection connection = null;
                try {
                    URL url = new URL(VERSION_URL);
                    connection = (HttpURLConnection) url.openConnection();
                    connection.setConnectTimeout(6000);
                    connection.setReadTimeout(6000);
                    connection.setRequestMethod("GET");
                    connection.setRequestProperty("Accept", "application/json");

                    int statusCode = connection.getResponseCode();
                    if (statusCode < 200 || statusCode >= 300) {
                        return;
                    }

                    BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), "UTF-8"));
                    StringBuilder payload = new StringBuilder();
                    String line;
                    while ((line = reader.readLine()) != null) {
                        payload.append(line);
                    }
                    reader.close();

                    JSONObject data = new JSONObject(payload.toString());
                    final int latestCode = data.optInt("latest_version_code", 0);
                    final int minSupportedCode = data.optInt("min_supported_version_code", 0);
                    final boolean forceUpdate = data.optBoolean("force_update", false) || getCurrentVersionCode() < minSupportedCode;
                    final String versionName = data.optString("latest_version_name", "");
                    final String downloadUrl = data.optString("download_url", BASE_URL + "android/download/");
                    final String message = data.optString("message", "Nueva version de Cardbook disponible.");
                    final String changelog = buildChangelog(data.optJSONArray("changelog"));

                    if (latestCode > getCurrentVersionCode()) {
                        runOnUiThread(new Runnable() {
                            @Override
                            public void run() {
                                showUpdateDialog(versionName, message, changelog, downloadUrl, forceUpdate);
                            }
                        });
                    }
                } catch (Exception ignored) {
                    // La app debe seguir funcionando aunque el chequeo de version falle.
                } finally {
                    if (connection != null) {
                        connection.disconnect();
                    }
                }
            }
        }).start();
    }

    private void showUpdateDialog(String versionName, String message, String changelog, final String downloadUrl, boolean forceUpdate) {
        String title = versionName.trim().length() > 0
            ? "Actualizacion disponible " + versionName
            : "Actualizacion disponible";
        String body = message;
        if (changelog.trim().length() > 0) {
            body += "\n\n" + changelog;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this)
            .setTitle(title)
            .setMessage(body)
            .setPositiveButton("Actualizar", new DialogInterface.OnClickListener() {
                @Override
                public void onClick(DialogInterface dialog, int which) {
                    openExternal(downloadUrl);
                }
            });

        if (!forceUpdate) {
            builder.setNegativeButton("Luego", null);
        }

        AlertDialog dialog = builder.create();
        dialog.setCanceledOnTouchOutside(!forceUpdate);
        dialog.setCancelable(!forceUpdate);
        dialog.show();
    }

    private String buildChangelog(JSONArray changelog) {
        if (changelog == null || changelog.length() == 0) {
            return "";
        }
        StringBuilder builder = new StringBuilder("Novedades:");
        for (int i = 0; i < changelog.length(); i++) {
            builder.append("\n- ").append(changelog.optString(i));
        }
        return builder.toString();
    }

    private int getCurrentVersionCode() {
        try {
            PackageInfo info = getPackageManager().getPackageInfo(getPackageName(), 0);
            return info.versionCode;
        } catch (Exception ignored) {
            return 0;
        }
    }

    private void openExternal(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception ignored) {
            Toast.makeText(this, "No se pudo abrir el enlace", Toast.LENGTH_SHORT).show();
        }
    }

    private void downloadFile(String url, String mimeType) {
        if (!isNetworkAvailable()) {
            Toast.makeText(this, "Sin conexion para descargar", Toast.LENGTH_SHORT).show();
            return;
        }

        try {
            Uri uri = Uri.parse(url);
            String extension = MimeTypeMap.getSingleton().getExtensionFromMimeType(mimeType);
            if (extension == null || extension.trim().length() == 0) {
                extension = url.toLowerCase(Locale.US).contains(".vcf") ? "vcf" : "download";
            }
            String fileName = "cardbook-" + System.currentTimeMillis() + "." + extension;

            DownloadManager.Request request = new DownloadManager.Request(uri);
            request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, fileName);
            request.setTitle("Cardbook");
            request.setDescription("Descargando archivo");
            request.addRequestHeader("Cookie", CookieManager.getInstance().getCookie(BASE_URL));

            DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
            if (manager != null) {
                manager.enqueue(request);
                Toast.makeText(this, "Descarga iniciada", Toast.LENGTH_SHORT).show();
            }
        } catch (Exception error) {
            openExternal(url);
        }
    }

    private void showOfflineScreen() {
        hideSplash();
        String status = isNetworkAvailable() ? "No pudimos cargar Cardbook ahora mismo." : "Tu telefono no tiene conexion a internet.";
        String html =
            "<!doctype html><html><head><meta name='viewport' content='width=device-width,initial-scale=1'>"
            + "<style>body{margin:0;font-family:Arial,sans-serif;background:#003875;color:#fff;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box}"
            + ".card{max-width:420px;background:#fff;color:#051630;border-radius:24px;padding:28px;box-shadow:0 24px 70px rgba(0,0,0,.24)}"
            + ".mark{width:64px;height:64px;border-radius:18px;background:#0057b8;color:#fff;display:grid;place-items:center;font-weight:800;font-size:28px;margin-bottom:18px}"
            + "h1{font-size:28px;margin:0 0 10px}p{line-height:1.55;color:#475569;margin:0 0 18px}"
            + "button,a{display:inline-block;border:0;border-radius:999px;background:#d8a441;color:#06234a;font-weight:800;padding:13px 18px;text-decoration:none;margin:4px 8px 0 0}"
            + ".ghost{background:#eaf1fb}</style></head><body><section class='card'><div class='mark'>C</div><h1>Cardbook no esta disponible</h1>"
            + "<p>" + status + " Revisa la conexion o intenta nuevamente.</p>"
            + "<button onclick=\"location.href='" + BASE_URL + "'\">Reintentar</button>"
            + "<button class='ghost' onclick=\"CardbookAndroid.openSettings()\">Ajustes</button></section></body></html>";
        webView.loadDataWithBaseURL(BASE_URL, html, "text/html", "UTF-8", null);
    }

    private boolean isNetworkAvailable() {
        ConnectivityManager manager = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (manager == null) return false;
        NetworkInfo info = manager.getActiveNetworkInfo();
        return info != null && info.isConnected();
    }

    private void hideSplash() {
        if (splashView != null) {
            splashView.setVisibility(View.GONE);
        }
    }

    private TextView navButton(String text, View.OnClickListener listener) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextColor(WHITE);
        view.setTextSize(13);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(12), 0, dp(12), 0);
        view.setBackground(rounded(Color.argb(32, 255, 255, 255), Color.argb(70, 255, 255, 255)));
        view.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, dp(40));
        params.setMargins(dp(8), 0, 0, 0);
        view.setLayoutParams(params);
        return view;
    }

    private GradientDrawable rounded(int color, int strokeColor) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(dp(999));
        drawable.setStroke(dp(1), strokeColor);
        return drawable;
    }

    private GradientDrawable gradient(int start, int end) {
        return new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, new int[]{start, end});
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density);
    }

    private int getStatusBarHeight() {
        int resourceId = getResources().getIdentifier("status_bar_height", "dimen", "android");
        if (resourceId > 0) {
            return getResources().getDimensionPixelSize(resourceId);
        }
        return 0;
    }

    public class AndroidBridge {
        @JavascriptInterface
        public void share(String title, String text, String url) {
            Intent intent = new Intent(Intent.ACTION_SEND);
            intent.setType("text/plain");
            String body = "";
            if (text != null && text.trim().length() > 0) {
                body += text.trim() + "\n";
            }
            if (url != null && url.trim().length() > 0) {
                body += url.trim();
            }
            intent.putExtra(Intent.EXTRA_SUBJECT, title == null ? "Cardbook" : title);
            intent.putExtra(Intent.EXTRA_TEXT, body.trim().length() == 0 ? BASE_URL : body.trim());
            startActivity(Intent.createChooser(intent, "Compartir con"));
        }

        @JavascriptInterface
        public void openSettings() {
            startActivity(new Intent(Settings.ACTION_WIRELESS_SETTINGS));
        }
    }
}
