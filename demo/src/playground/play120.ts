// 「彈奏全部120鍵」 — a showcase specimen that lights EVERY one of the
// font's 120 unicode-range slices at once. Four keys are font-internal and cannot be
// reached by a normal paste: slice 8 holds only CJK-compatibility ideographs (a pasted
// 樂 U+6A02 lands on slice 118; the compat 樂 U+F914 here lands on 8), and slices 9-11
// are pure Private-Use (no character at all). They survive only because this text is
// injected via textContent — which does NOT NFC-normalise — with those codepoints written
// as explicit \u escapes. Built + verified against sliceTable.json (see scripts).

export const PLAY_ALL_TITLE = '一百二十鍵'

export const PLAY_ALL_BODY = [
  '<p>清晨，我坐在這架字體鋼琴前，想把一百二十枚琴鍵逐一按響。每一枚切片都是一個音，藏在傳承字形的骨架裡。指尖落下，戶的點、骨的折、青的底、過的走之，逐一亮起。翻閱古籍、查考源流，方見漢字一筆一畫的價值——這份端正，值得細品。窗邊沏一壺清茶，涵育心性，案頭一塵不染、不沾纖污。字形自故鄉啟程，跨越百年；縱使落於矽片，光影明滅，仍一筆不苟。偶有生僻如「汆」者也一併入鍵，按到趣處，不禁「唷」地輕呼一聲。從台北到倫敦，由鉛字到螢幕，書寫不斷改變，對美的講究始終如一；橫豎撇捺之間，載著前人的情感與溫度，言語靜靜流動，從不間斷——這架琴奏的，正是一闋無聲之\uf914。</p>',
  '<p>於是這架琴以萬國之聲應和——<br>日本語：ひらがな と カタカナ、ｱｲｳｴｵ、むぜゐ。<br>한국어: 안녕하세요, 반갑습니다.<br>English & Español: heritage glyphs sing; ¡olé!<br>Tiếng Việt: Chào, tự do, đường — Ư。音標：ˈka。<br>ไทย: สวัสดี。বাংলা: নমস্কার。العربية: سلام。עברית: שלום。ኢትዮ: ሰላም。<br>記號齊鳴：♪ ♬ ☼ ☽ ↔ ⇄ ╬ ▦ ⑴⑵⑶ ❉ ✺ ⚓ ☎ §¶。<br>眾鍵同響：🤣🎹🎶🎵😊🌙📜👌🌟📨🎯🌞🤝</p>',
  '<p>指尖再從容掠過琴身深處那些生僻的鍵，像一道綿長的刮奏：촌웅덀鴴鯓驯餒韆陎鏤鋥釰邻轨踘賁譬觶袛蝌蘂蒱荸艮脓羱纯綉簠竻禈础眅痌璚玳牿焓濨滖淓泚殻樱椀柙暧敝搧懆悬彸帴峠宀婑夋垡噯啑吽勛冏倲伢丂ᆯ丑乖丈。</p>',
  '<p>餘下三枚私用區之鍵，無字可循，僅以原始碼點觸及，故呈空白：\uf06e\ue658\ue18e</p>',
].join('')
