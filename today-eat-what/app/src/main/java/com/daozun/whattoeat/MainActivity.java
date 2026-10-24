package com.daozun.whattoeat;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.widget.Toast;
import android.text.InputFilter;
import org.json.JSONArray;
import org.json.JSONObject;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Random;
import java.util.Set;

public class MainActivity extends Activity {
    private static final int BG = Color.rgb(255, 250, 244);
    private static final int INK = Color.rgb(58, 48, 44);
    private static final int MUTED = Color.rgb(133, 120, 113);
    private static final int ACCENT = Color.rgb(236, 108, 87);
    private static final int LIGHT = Color.rgb(255, 236, 226);
    private static final String[] TYPES = {"全部", "早餐", "午餐", "晚餐"};
    private final Random random = new Random();
    private final ArrayList<Meal> menu = new ArrayList<>();
    private final ArrayList<Meal> custom = new ArrayList<>();
    private final ArrayList<String> recent = new ArrayList<>();
    private final TextView[] pills = new TextView[4];
    private SharedPreferences prefs;
    private TextView resultName, resultType, resultHint, favoriteButton, countLabel;
    private Meal current;
    private int selectedType = 0;

    static class Meal {
        final String name;
        final String type;
        final boolean isCustom;
        Meal(String n, String t, boolean c) { name=n; type=t; isCustom=c; }
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(Color.rgb(255, 244, 235));
        getWindow().setNavigationBarColor(BG);
        getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        prefs = getSharedPreferences("today_eat_what_v1", MODE_PRIVATE);
        addDefaults();
        loadCustom();
        loadRecent();
        drawUI();
        pick();
    }

    private void addGroup(String category, String csv) {
        for (String entry : csv.split("、")) menu.add(new Meal(entry, category, false));
    }

    private void addDefaults() {
        addGroup("早餐", "豆漿油條、鮮肉包、蔥油餅、皮蛋瘦肉粥、蛋餅、飯糰、饅頭夾蛋、小籠包、燒餅夾蛋、三明治、法式吐司、牛奶燕麥、雞蛋羹、紅豆麵包、饅頭配豆漿、水煮蛋與地瓜、鍋貼、米粉湯、餛飩湯、蘿蔔糕、雜糧粥、蛋沙拉吐司、玉米濃湯、芝麻湯圓");
        addGroup("午餐", "牛肉麵、滷肉飯、雞腿便當、番茄炒蛋飯、咖哩雞飯、鍋燒意麵、酸辣粉、紅燒牛肉飯、麻婆豆腐飯、排骨飯、雞肉沙拉、香菇雞湯麵、日式豬排飯、壽司、韓式拌飯、餃子、燴飯、台式炒麵、肉燥乾麵、番茄義大利麵、炒河粉、蛋炒飯、酸菜魚米線、雞絲涼麵");
        addGroup("晚餐", "麻辣火鍋、酸菜魚、水煮牛肉、宮保雞丁、魚香肉絲、麻婆豆腐、番茄牛腩、清蒸魚、蒜香蝦、烤雞腿、壽喜燒、韓式烤肉、涮羊肉、菌菇湯鍋、海鮮粥、椒鹽排骨、回鍋肉、香菇燉雞、紅燒肉、砂鍋豆腐、炒時蔬配米飯、番茄燉蛋、蔥燒豆腐、烤魚");
    }

    private int dp(float n) { return (int)(n*getResources().getDisplayMetrics().density+0.5f); }

    private GradientDrawable shape(int color, int radius) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(color);
        d.setCornerRadius(dp(radius));
        return d;
    }

    private TextView label(String s, int sp, int color, boolean bold) {
        TextView v=new TextView(this);
        v.setText(s); v.setTextSize(sp); v.setTextColor(color);
        if (bold) v.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return v;
    }

    private LinearLayout vertical() {
        LinearLayout v=new LinearLayout(this); v.setOrientation(LinearLayout.VERTICAL); return v;
    }

    private LinearLayout.LayoutParams block(int top) {
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1, -2);
        p.topMargin=dp(top); return p;
    }

    private TextView button(String text, boolean primary) {
        TextView b=label(text, 16, primary?Color.WHITE:INK, true);
        b.setGravity(Gravity.CENTER);
        b.setPadding(dp(14),dp(16),dp(14),dp(16));
        b.setBackground(shape(primary?ACCENT:LIGHT, 18));
        b.setClickable(true);
        return b;
    }

    private void drawUI() {
        ScrollView scroll=new ScrollView(this);
        scroll.setBackgroundColor(BG);
        scroll.setFillViewport(true);
        scroll.setClipToPadding(false);
        LinearLayout root=vertical();
        root.setPadding(dp(23),dp(31),dp(23),dp(30));
        scroll.addView(root);

        TextView eyebrow=label(new SimpleDateFormat("M 月 d 日 · EEEE", Locale.TAIWAN).format(new java.util.Date()), 13, MUTED, false);
        root.addView(eyebrow);
        TextView h1=label("今天吃什麼？", 32, INK, true);
        root.addView(h1, block(10));
        TextView sub=label("每天最難的選擇，交給一點點好運。 ✨", 14, MUTED, false);
        root.addView(sub, block(8));

        TextView chooseLabel=label("先選一餐", 15, INK, true);
        root.addView(chooseLabel, block(35));
        LinearLayout chips=new LinearLayout(this);
        chips.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(chips, block(13));
        for (int i=0;i<TYPES.length;i++) {
            final int index=i;
            TextView chip=label(TYPES[i], 14, INK, true);
            chip.setGravity(Gravity.CENTER);
            chip.setPadding(0,dp(12),0,dp(12));
            LinearLayout.LayoutParams cp=new LinearLayout.LayoutParams(0,-2,1);
            if (i>0) cp.leftMargin=dp(7);
            chips.addView(chip,cp);
            chip.setOnClickListener(v->{selectedType=index; updateChips(); pick();});
            pills[i]=chip;
        }
        updateChips();

        LinearLayout card=vertical();
        card.setGravity(Gravity.CENTER);
        card.setPadding(dp(18),dp(30),dp(18),dp(30));
        GradientDrawable cardBg=shape(Color.WHITE,26);
        cardBg.setStroke(dp(1),Color.rgb(249,231,221));
        card.setBackground(cardBg);
        card.setElevation(dp(3));
        root.addView(card, block(24));

        TextView cardTitle=label("🍽  今天就吃這個", 15, MUTED, true);
        card.addView(cardTitle);
        resultName=label("", 34, INK, true);
        resultName.setGravity(Gravity.CENTER);
        resultName.setMinHeight(dp(91));
        resultName.setGravity(Gravity.CENTER);
        card.addView(resultName, block(10));
        resultType=label("", 13, ACCENT, true);
        resultType.setPadding(dp(20),dp(8),dp(20),dp(8));
        resultType.setBackground(shape(LIGHT,40));
        card.addView(resultType, block(8));
        resultHint=label("好好吃飯，就是今天的小幸福。", 13, MUTED, false);
        resultHint.setGravity(Gravity.CENTER);
        card.addView(resultHint, block(21));

        TextView draw=button("🎲   幫我決定", true);
        root.addView(draw,block(24));
        draw.setOnClickListener(v->pick());

        LinearLayout row=new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        root.addView(row,block(10));
        TextView reroll=button("再抽一次 ↻", false);
        favoriteButton=button("♡  加入收藏",false);
        LinearLayout.LayoutParams half=new LinearLayout.LayoutParams(0,-2,1);
        row.addView(reroll,half);
        LinearLayout.LayoutParams half2=new LinearLayout.LayoutParams(0,-2,1);
        half2.leftMargin=dp(10);
        row.addView(favoriteButton,half2);
        reroll.setOnClickListener(v->pick());
        favoriteButton.setOnClickListener(v->toggleFavorite());

        TextView tools=label("我的口袋菜單", 15, INK, true);
        root.addView(tools,block(34));
        countLabel=label("",13,MUTED,false);
        root.addView(countLabel,block(8));
        updateCount();

        TextView add=button("＋   新增自訂餐點",false);
        root.addView(add,block(15));
        add.setOnClickListener(v->addCustomDialog());
        LinearLayout toolRow=new LinearLayout(this);
        root.addView(toolRow,block(10));
        TextView favs=button("♥  我的收藏",false);
        TextView manage=button("☰  管理自訂",false);
        toolRow.addView(favs,new LinearLayout.LayoutParams(0,-2,1));
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(0,-2,1);p.leftMargin=dp(10);
        toolRow.addView(manage,p);
        favs.setOnClickListener(v->showFavorites());
        manage.setOnClickListener(v->manageCustom());

        TextView footer=label("不用登入 · 不用網路 · 資料只存在你的手機",12,MUTED,false);
        footer.setGravity(Gravity.CENTER);
        root.addView(footer,block(36));
        setContentView(scroll);
    }

    private void updateChips() {
        for (int i=0;i<pills.length;i++){
            TextView t=pills[i]; if(t==null)continue;
            boolean active=i==selectedType;
            t.setTextColor(active?Color.WHITE:MUTED);
            t.setBackground(shape(active?ACCENT:Color.rgb(248,238,230),18));
        }
    }

    private void updateCount() {
        if (countLabel!=null) countLabel.setText("內建 "+menu.size()+" 道料理・自訂 "+custom.size()+" 道");
    }

    private ArrayList<Meal> filtered() {
        ArrayList<Meal> options=new ArrayList<>();
        for(Meal m:menu)if(selectedType==0||m.type.equals(TYPES[selectedType]))options.add(m);
        for(Meal m:custom)if(selectedType==0||m.type.equals(TYPES[selectedType]))options.add(m);
        return options;
    }

    private void pick() {
        ArrayList<Meal> all=filtered();
        if(all.isEmpty()){current=null;render();return;}
        ArrayList<Meal> fresh=new ArrayList<>();
        for(Meal m:all) if(!recent.contains(m.name))fresh.add(m);
        if(fresh.isEmpty())fresh=all;
        current=fresh.get(random.nextInt(fresh.size()));
        trackCurrent();
        render();
    }

    private void trackCurrent() {
        if(current==null)return;
        recent.remove(current.name);
        recent.add(0,current.name);
        while(recent.size()>4)recent.remove(recent.size()-1);
        JSONArray a=new JSONArray();
        for(String s:recent)a.put(s);
        prefs.edit().putString("recent",a.toString()).apply();
    }

    private void render() {
        if(resultName==null)return;
        resultName.setText(current==null?"菜單是空的":current.name);
        resultType.setText(current==null?"":"✦  "+current.type+"  ✦");
        resultHint.setText(current==null?"新增一個餐點試試吧":"好好吃飯，就是今天的小幸福。");
        if(favoriteButton!=null)favoriteButton.setText(current!=null&&getFavorites().contains(current.name)?"♥  已收藏":"♡  加入收藏");
    }

    private Set<String> getFavorites() {
        return new HashSet<>(prefs.getStringSet("favorites",new HashSet<>()));
    }

    private void toggleFavorite(){
        if(current==null)return;
        Set<String> s=getFavorites();
        if(!s.add(current.name)){s.remove(current.name);Toast.makeText(this,"已從收藏移除",Toast.LENGTH_SHORT).show();}
        else Toast.makeText(this,"已加入收藏 ♥",Toast.LENGTH_SHORT).show();
        prefs.edit().putStringSet("favorites",s).apply();
        render();
    }

    private void addCustomDialog(){
        LinearLayout content=vertical();
        content.setPadding(dp(24),dp(10),dp(24),dp(2));
        EditText input=new EditText(this);
        input.setSingleLine(true);
        input.setTextSize(17);
        input.setHint("例如：媽媽做的紅燒肉");
        input.setFilters(new InputFilter[]{new InputFilter.LengthFilter(24)});
        content.addView(input,new LinearLayout.LayoutParams(-1,-2));
        TextView hint=label("餐點類型",14,MUTED,false);
        content.addView(hint,block(18));
        Spinner spinner=new Spinner(this);
        String[] categories={"早餐","午餐","晚餐"};
        spinner.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,categories));
        content.addView(spinner,block(5));
        AlertDialog dialog=new AlertDialog.Builder(this)
           .setTitle("新增我的拿手菜")
           .setView(content)
           .setNegativeButton("取消",null)
           .setPositiveButton("加入菜單",null).create();
        dialog.setOnShowListener(v->dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(w->{
            String name=input.getText().toString().trim();
            if(name.isEmpty()){input.setError("請先輸入餐點名稱");return;}
            for(Meal m:menu)if(m.name.equals(name)){input.setError("內建菜單已經有這道菜");return;}
            for(Meal m:custom)if(m.name.equals(name)){input.setError("自訂菜單已有這道菜");return;}
            Meal m=new Meal(name,categories[spinner.getSelectedItemPosition()],true);
            custom.add(m);saveCustom();updateCount();
            selectedType=0;updateChips();current=m;trackCurrent();render();
            Toast.makeText(this,"已加入自訂菜單",Toast.LENGTH_SHORT).show();
            dialog.dismiss();
        }));
        dialog.show();
    }

    private void showFavorites(){
        Set<String> favorites=getFavorites();
        ArrayList<Meal> list=new ArrayList<>();
        for(Meal m:menu)if(favorites.contains(m.name))list.add(m);
        for(Meal m:custom)if(favorites.contains(m.name))list.add(m);
        if(list.isEmpty()){new AlertDialog.Builder(this).setTitle("我的收藏")
            .setMessage("這裡還是空的。抽到喜歡的餐點，點「加入收藏」吧！")
            .setPositiveButton("知道了",null).show();return;}
        String[] names=new String[list.size()];
        for(int i=0;i<names.length;i++)names[i]=list.get(i).name+"  ·  "+list.get(i).type;
        new AlertDialog.Builder(this).setTitle("♥ 我的收藏")
            .setItems(names,(d,which)->{selectedType=0;updateChips();current=list.get(which);trackCurrent();render();})
            .setNegativeButton("關閉",null).show();
    }

    private void manageCustom(){
        if(custom.isEmpty()){new AlertDialog.Builder(this).setTitle("管理自訂菜單")
          .setMessage("還沒有自訂餐點，點「新增自訂餐點」就能加入。")
          .setPositiveButton("好的",null).show();return;}
        String[] names=new String[custom.size()];
        for(int i=0;i<names.length;i++)names[i]=custom.get(i).name+"  ·  "+custom.get(i).type;
        new AlertDialog.Builder(this).setTitle("管理自訂菜單 · 點選刪除")
            .setItems(names,(d,index)->{
                Meal toDelete=custom.get(index);
                new AlertDialog.Builder(this).setTitle("刪除「"+toDelete.name+"」？")
                    .setMessage("只會刪除這道自訂餐點。")
                    .setNegativeButton("取消",null)
                    .setPositiveButton("確認刪除",(dd,w)->{
                        custom.remove(toDelete);saveCustom();updateCount();
                        if(current==toDelete)pick();
                        Toast.makeText(this,"已刪除",Toast.LENGTH_SHORT).show();
                    }).show();
            }).setNegativeButton("關閉",null).show();
    }

    private void loadCustom(){
        try{
            JSONArray a=new JSONArray(prefs.getString("custom","[]"));
            for(int i=0;i<a.length();i++){
                JSONObject o=a.getJSONObject(i);
                String name=o.optString("name","").trim(),type=o.optString("type","");
                if(!name.isEmpty()&&(type.equals("早餐")||type.equals("午餐")||type.equals("晚餐")))
                    custom.add(new Meal(name,type,true));
            }
        }catch(Exception ignored){}
    }

    private void saveCustom(){
        JSONArray a=new JSONArray();
        for(Meal m:custom){
            JSONObject o=new JSONObject();
            try{o.put("name",m.name);o.put("type",m.type);a.put(o);}catch(Exception ignored){}
        }
        prefs.edit().putString("custom",a.toString()).apply();
    }

    private void loadRecent(){
        try{
            JSONArray a=new JSONArray(prefs.getString("recent","[]"));
            for(int i=0;i<a.length();i++)recent.add(a.getString(i));
        }catch(Exception ignored){}
    }
}
