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
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

public class MainActivity extends Activity {
    private static final int BLUE = Color.rgb(0, 87, 184);
    private static final int BLUE_DARK = Color.rgb(0, 56, 117);
    private static final int GOLD = Color.rgb(216, 164, 65);
    private static final int WHITE = Color.WHITE;
    private static final int MUTED = Color.rgb(99, 113, 137);
    private static final String WEB_URL = "https://cardbook-45cf0409dc07.herokuapp.com/";
    private static final String API_URL = WEB_URL + "api/v1/";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        renderHome();
    }

    private void renderHome() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.rgb(244, 246, 249));

        TextView header = new TextView(this);
        header.setText("Cardbook");
        header.setTextColor(WHITE);
        header.setTextSize(24);
        header.setTypeface(Typeface.DEFAULT_BOLD);
        header.setGravity(Gravity.CENTER_VERTICAL);
        header.setPadding(dp(22), dp(18), dp(22), dp(18));
        header.setBackground(gradient(BLUE_DARK, BLUE));
        root.addView(header, new LinearLayout.LayoutParams(-1, dp(74)));

        ScrollView scroll = new ScrollView(this);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(20), dp(22), dp(20), dp(24));
        scroll.addView(body);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));

        body.addView(heroCard());
        body.addView(actionGrid());
        body.addView(infoCard("API conectada", "La app consume la API REST de Cardbook para empresas, perfiles digitales, Book, publicaciones y alianzas."));
        body.addView(infoCard("Version inicial", "Este APK abre los servicios principales y queda preparado para seguir integrando CRUD nativo pantalla por pantalla."));

        setContentView(root);
    }

    private View heroCard() {
        LinearLayout card = panel(BLUE_DARK);
        TextView badge = small("APP ANDROID");
        badge.setTextColor(GOLD);
        TextView title = new TextView(this);
        title.setText("Tarjetas digitales inteligentes");
        title.setTextColor(WHITE);
        title.setTextSize(31);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setPadding(0, dp(8), 0, dp(8));
        TextView copy = paragraph("Gestiona Cardbook desde tu telefono: empresas, tarjetas, QR, Book y alianzas en una experiencia movil.");
        copy.setTextColor(Color.argb(220, 255, 255, 255));
        card.addView(badge);
        card.addView(title);
        card.addView(copy);
        card.addView(button("Abrir plataforma", GOLD, BLUE_DARK, new View.OnClickListener() {
            @Override public void onClick(View v) { openUrl(WEB_URL); }
        }));
        return card;
    }

    private View actionGrid() {
        LinearLayout wrap = new LinearLayout(this);
        wrap.setOrientation(LinearLayout.VERTICAL);
        wrap.setPadding(0, dp(10), 0, 0);
        wrap.addView(row(button("Dashboard", BLUE, WHITE, new View.OnClickListener() {
            @Override public void onClick(View v) { openUrl(WEB_URL + "dashboard/"); }
        }), button("Book", BLUE, WHITE, new View.OnClickListener() {
            @Override public void onClick(View v) { openUrl(WEB_URL + "dashboard/book/"); }
        })));
        wrap.addView(row(button("API", WHITE, BLUE_DARK, new View.OnClickListener() {
            @Override public void onClick(View v) { openUrl(API_URL); }
        }), button("Login", WHITE, BLUE_DARK, new View.OnClickListener() {
            @Override public void onClick(View v) { openUrl(WEB_URL + "login/"); }
        })));
        return wrap;
    }

    private LinearLayout row(View a, View b) {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setPadding(0, 0, 0, dp(10));
        row.addView(a, new LinearLayout.LayoutParams(0, dp(54), 1));
        View gap = new View(this);
        row.addView(gap, new LinearLayout.LayoutParams(dp(10), 1));
        row.addView(b, new LinearLayout.LayoutParams(0, dp(54), 1));
        return row;
    }

    private View infoCard(String titleText, String bodyText) {
        LinearLayout card = panel(WHITE);
        TextView title = new TextView(this);
        title.setText(titleText);
        title.setTextColor(BLUE_DARK);
        title.setTextSize(18);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        TextView body = paragraph(bodyText);
        body.setTextColor(MUTED);
        card.addView(title);
        card.addView(body);
        return card;
    }

    private LinearLayout panel(int color) {
        LinearLayout card = new LinearLayout(this);
        card.setOrientation(LinearLayout.VERTICAL);
        card.setPadding(dp(20), dp(18), dp(20), dp(18));
        card.setBackground(rounded(color, 1, Color.argb(30, 0, 87, 184), dp(12)));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.setMargins(0, 0, 0, dp(14));
        card.setLayoutParams(params);
        card.setElevation(dp(2));
        return card;
    }

    private TextView paragraph(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(15);
        view.setLineSpacing(2, 1.05f);
        view.setPadding(0, dp(4), 0, dp(14));
        return view;
    }

    private TextView small(String text) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(12);
        view.setTypeface(Typeface.DEFAULT_BOLD);
        return view;
    }

    private Button button(String text, int bg, int fg, View.OnClickListener listener) {
        Button button = new Button(this);
        button.setText(text);
        button.setTextColor(fg);
        button.setTypeface(Typeface.DEFAULT_BOLD);
        button.setTextSize(14);
        button.setAllCaps(false);
        button.setBackground(rounded(bg, 0, bg, dp(999)));
        button.setOnClickListener(listener);
        return button;
    }

    private void openUrl(String url) {
        startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
    }

    private GradientDrawable rounded(int color, int strokeWidth, int strokeColor, int radius) {
        GradientDrawable drawable = new GradientDrawable();
        drawable.setColor(color);
        drawable.setCornerRadius(radius);
        if (strokeWidth > 0) drawable.setStroke(dp(strokeWidth), strokeColor);
        return drawable;
    }

    private GradientDrawable gradient(int start, int end) {
        return new GradientDrawable(GradientDrawable.Orientation.LEFT_RIGHT, new int[]{start, end});
    }

    private int dp(int value) {
        return (int) (value * getResources().getDisplayMetrics().density);
    }
}
