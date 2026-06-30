package com.cardbook.app;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int BLUE = Color.rgb(0, 87, 184);
    private static final int BLUE_DARK = Color.rgb(0, 56, 117);
    private static final int GOLD = Color.rgb(216, 164, 65);
    private static final int WHITE = Color.WHITE;
    private static final String BASE_URL = "https://cardbook-45cf0409dc07.herokuapp.com/";

    private WebView webView;
    private ProgressBar progressBar;
    private TextView titleView;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        renderWebApp();
        if (savedInstanceState == null) {
            webView.loadUrl(BASE_URL);
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        webView.saveState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
            return;
        }
        super.onBackPressed();
    }

    private void renderWebApp() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(244, 246, 249));

        LinearLayout appBar = new LinearLayout(this);
        appBar.setOrientation(LinearLayout.HORIZONTAL);
        appBar.setGravity(Gravity.CENTER_VERTICAL);
        appBar.setPadding(dp(16), dp(10), dp(12), dp(10));
        appBar.setBackground(gradient(BLUE_DARK, BLUE));

        titleView = new TextView(this);
        titleView.setText("Cardbook");
        titleView.setTextColor(WHITE);
        titleView.setTextSize(20);
        titleView.setTypeface(Typeface.DEFAULT_BOLD);
        titleView.setSingleLine(true);
        appBar.addView(titleView, new LinearLayout.LayoutParams(0, dp(48), 1));

        appBar.addView(navButton("Inicio", new View.OnClickListener() {
            @Override public void onClick(View view) { webView.loadUrl(BASE_URL); }
        }));
        appBar.addView(navButton("Login", new View.OnClickListener() {
            @Override public void onClick(View view) { webView.loadUrl(BASE_URL + "login/"); }
        }));

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setProgress(0);
        progressBar.setVisibility(View.GONE);

        FrameLayout webFrame = new FrameLayout(this);
        webView = new WebView(this);
        configureWebView();
        webFrame.addView(webView, new FrameLayout.LayoutParams(-1, -1));

        root.addView(appBar, new LinearLayout.LayoutParams(-1, dp(68)));
        root.addView(progressBar, new LinearLayout.LayoutParams(-1, dp(3)));
        root.addView(webFrame, new LinearLayout.LayoutParams(-1, 0, 1));
        setContentView(root);
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

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                progressBar.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
                progressBar.setProgress(newProgress);
                super.onProgressChanged(view, newProgress);
            }

            @Override
            public void onReceivedTitle(WebView view, String title) {
                if (title != null && title.trim().length() > 0) {
                    titleView.setText("Cardbook");
                }
                super.onReceivedTitle(view, title);
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
        });

        webView.setDownloadListener(new DownloadListener() {
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {
                openExternal(url);
                Toast.makeText(MainActivity.this, "Descarga abierta en el navegador", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private boolean handleUrl(String url) {
        if (url == null) return false;
        if (url.startsWith(BASE_URL) || url.startsWith("https://cardbook-45cf0409dc07.herokuapp.com")) {
            return false;
        }
        if (url.startsWith("tel:") || url.startsWith("mailto:") || url.startsWith("sms:") || url.startsWith("https://wa.me/")) {
            openExternal(url);
            return true;
        }
        if (url.startsWith("http://") || url.startsWith("https://")) {
            openExternal(url);
            return true;
        }
        return false;
    }

    private void openExternal(String url) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
        } catch (Exception ignored) {
            Toast.makeText(this, "No se pudo abrir el enlace", Toast.LENGTH_SHORT).show();
        }
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
}
