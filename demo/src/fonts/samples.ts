// Per-script specimen samples — the playground swaps the editable specimen to the
// matching script when the chosen font's script changes (TC / SC / JP). `body` is
// HTML so the paragraph structure survives.
import type { Script } from './fonts'

export type Sample = { readonly title: string; readonly body: string }

export const SAMPLES: Record<Script, Sample> = {
  tc: {
    title: '字裡行間的傳承',
    body:
      '<p>清晨的台北，捷運緩緩駛過城市的骨幹，車窗外的天色由青轉亮。月台上，旅客的情緒交織成一片低語，有人讀著手中的書，有人望向遠方的海角。文字像一條無形的絲線，把過去與現在織在一起。每個字的形體，都承載著前人的講究與情感。</p>' +
      '<p>從英國到台北，從鉛字到螢幕，書寫的方式不斷改變，對美的追求卻始終如一。傳承字形所展現的，正是這份對細節的尊重——戶的寫法、骨的轉折、直的橫豎、青的結構、過的走之，無一不在訴說漢字悠長的歷史。當我們重新端詳這些字，彷彿能聽見時間的回響，看見文化在筆畫間靜靜流動，言語與書藝交融，從不間斷。</p>',
  },
  sc: {
    title: '字里行间的传承',
    body:
      '<p>清晨的台北，地铁缓缓驶过城市的骨干，车窗外的天色由青转亮。月台上，旅客的情绪交织成一片低语，有人读着手中的书，有人望向远方的海角。文字像一条无形的丝线，把过去与现在织在一起；每个字的形体，都承载着前人的讲究与情感。</p>' +
      '<p>从英国到台北，从铅字到屏幕，书写的方式不断改变，对美的追求却始终如一。传承字形所展现的，正是这份对细节的尊重，户骨直过青，无一不在诉说汉字悠长的历史，言语与书艺交融，从不间断。</p>',
  },
  jp: {
    title: '文字の継承',
    body:
      '<p>春はあけぼの。やうやう白くなりゆく山際、少し明かりて、紫だちたる雲の細くたなびきたる。文字は時を越えて受け継がれ、筆の運びに先人の心が宿る。</p>' +
      '<p>仮名と漢字が織りなす言葉の美しさ、骨格の確かさ、青く澄んだ余白の情緒——その一つ一つに、書の歴史が静かに息づいてゐる。いま一度、この字たちを味はひたい。</p>',
  },
}
