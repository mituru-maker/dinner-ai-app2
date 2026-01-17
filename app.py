import streamlit as st
import google.generativeai as genai
from google.generativeai import GenerativeModel
import os
import time

def get_api_key():
    """APIキーを取得する関数"""
    # まず st.secrets を確認（例外処理を追加）
    try:
        secrets = st.secrets
        if "GOOGLE_API_KEY" in secrets:
            return secrets["GOOGLE_API_KEY"]
    except Exception:
        pass
    
    # なければサイドバーで入力
    st.sidebar.warning("⚠️ GOOGLE_API_KEY が secrets に見つかりません")
    api_key = st.sidebar.text_input(
        "Google API Key を入力してください",
        type="password",
        help="Google AI Studio で取得した API キーを入力してください"
    )
    
    if api_key:
        st.sidebar.success("✅ API キーが設定されました")
        return api_key
    else:
        st.sidebar.error("❌ API キーが必要です")
        return None

def initialize_gemini(api_key):
    """Gemini を初期化する関数"""
    try:
        # APIキーのデバッグ情報
        st.sidebar.write(f"🔑 APIキー確認: {api_key[:10]}...{api_key[-10:] if len(api_key) > 20 else '***'}")
        
        # デフォルト設定で初期化（APIバージョン指定なし）
        genai.configure(api_key=api_key)
        
        # 利用可能なモデルを確認
        models = list(genai.list_models())  # generator を list に変換
        
        # 利用可能なモデルを表示
        st.sidebar.subheader("🔍 利用可能なモデル")
        for model in models:
            model_name = model.name.split('/')[-1]
            supported_methods = getattr(model, 'supported_generation_methods', [])
            st.sidebar.text(f"• {model_name}: {supported_methods}")
        
        # generateContent をサポートするモデルを探す
        supported_models = []
        for model in models:
            if hasattr(model, 'supported_generation_methods') and 'generateContent' in model.supported_generation_methods:
                model_name = model.name.split('/')[-1]
                supported_models.append(model_name)
                st.sidebar.write(f"✅ サポート: {model_name}")
        
        # デバッグ：すべてのモデルの supported_generation_methods を表示
        st.sidebar.subheader("🔍 デバッグ情報")
        for model in models[:10]:  # 最初の10モデルのみ表示
            model_name = model.name.split('/')[-1]
            methods = getattr(model, 'supported_generation_methods', [])
            st.sidebar.text(f"{model_name}: {methods}")
        
        if not supported_models:
            st.error("❌ generateContent をサポートするモデルが見つかりません")
            st.sidebar.error("generateContent をサポートするモデルがありません")
            return None
        
        # 優先順位でモデルを選択（指定モデルを優先）
        priority_models = ['gemini-3-flash-preview', 'gemini-2.5-flash', 'gemini-2.0-flash', 'gemini-pro-latest']
        selected_model = None
        
        for priority in priority_models:
            if priority in supported_models:
                selected_model = priority
                break
        
        if not selected_model:
            # 最初の利用可能なモデルを使用
            selected_model = supported_models[0]
            st.warning(f"⚠️ 優先モデルが見つかりません。{selected_model} を使用します。")
        else:
            st.success(f"✅ {selected_model} を使用します")
        model = GenerativeModel(selected_model)
        return model
            
    except Exception as e:
        st.error(f"Gemini の初期化に失敗しました: {e}")
        st.sidebar.error(f"エラー詳細: {str(e)}")
        return None

def generate_dinner_suggestion(model, ingredients, cuisine_type):
    """晩ごはん提案を生成する関数"""
    prompt = f"""
以下の情報を基に、美味しい晩ごはん料理を提案してください。

【食材】
- 食材1: {ingredients[0] if ingredients[0] else "未指定"}
- 食材2: {ingredients[1] if ingredients[1] else "未指定"}
- 食材3: {ingredients[2] if ingredients[2] else "未指定"}

【料理ジャンル】
{cuisine_type}

【提案形式】
以下の形式で提案してください：

1. 料理名
2. 材料（リスト形式）
3. 簡単な作り方（手順を番号で）
4. AIのワンポイントアドバイス

食材を効果的に活用し、{cuisine_type}の特色を生かした料理を提案してください。
未指定の食材は、料理に合うものを自由に追加してください。
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"AIの応答生成中にエラーが発生しました: {e}")
        st.sidebar.error(f"生成エラー詳細: {str(e)}")
        
        # タイムアウトの可能性がある場合
        if "timeout" in str(e).lower() or "deadline" in str(e).lower():
            st.warning("⏰ タイムアウトしました。少し時間を置いて再度お試しください。")
        
        return None

def main():
    st.set_page_config(
        page_title="AI晩ごはん提案アプリ",
        page_icon="🍳",
        layout="centered"
    )
    
    st.title("🍳 AI晩ごはん提案アプリ")
    st.markdown("---")
    
    # APIキーの取得
    api_key = get_api_key()
    
    if not api_key:
        st.warning("⚠️ APIキーを設定してください")
        st.stop()
    
    # Geminiの初期化
    model = initialize_gemini(api_key)
    
    if not model:
        st.error("❌ AIモデルの初期化に失敗しました")
        st.stop()
    
    # 入力フォーム
    st.subheader("📝 料理の条件を入力")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ingredient1 = st.text_input("食材 1", placeholder="例：鶏肉")
    
    with col2:
        ingredient2 = st.text_input("食材 2", placeholder="例：玉ねぎ")
    
    with col3:
        ingredient3 = st.text_input("食材 3", placeholder="例：人参")
    
    cuisine_type = st.selectbox(
        "料理ジャンル",
        ["和食", "洋食", "中華", "イタリアン", "メキシカン", "韓国料理", "インド料理", "その他"],
        index=0
    )
    
    # 生成ボタン
    if st.button("🍽️ 晩ごはんを提案！", type="primary"):
        ingredients = [ingredient1, ingredient2, ingredient3]
        
        # すべての食材が空の場合の警告
        if not any(ingredients):
            st.warning("⚠️ 少なくとも1つの食材を入力してください")
            return
        
        with st.spinner("🤖 AIが料理を考えています..."):
            suggestion = generate_dinner_suggestion(model, ingredients, cuisine_type)
            
            if suggestion:
                st.success("✅ 料理提案が完了しました！")
                st.markdown("---")
                st.subheader("🍽️ AIからの提案")
                
                # 提案内容を表示
                st.markdown(suggestion)
                
                # コピーボタン
                st.markdown("---")
                if st.button("📋 提案をクリップボードにコピー"):
                    st.write("提案内容をコピーしました（ブラウザの機能を使用してください）")
    
    # 使い方
    with st.expander("📖 使い方"):
        st.markdown("""
        1. **APIキーの設定**: 
           - Streamlit Cloud の場合は secrets に `GOOGLE_API_KEY` を設定
           - ローカルの場合はサイドバーから手動入力
        
        2. **食材の入力**: 
           - 3つの食材を入力（未入力でも可）
           - 冷蔵庫にある食材などを入力
        
        3. **料理ジャンルの選択**: 
           - 好みの料理ジャンルを選択
        
        4. **提案の生成**: 
           - 「晩ごはんを提案！」ボタンをクリック
           - AIが料理名、材料、作り方、アドバイスを提案
        """)

if __name__ == "__main__":
    main()
