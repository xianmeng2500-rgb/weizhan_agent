import api from '@/api'

interface ShareConfig {
  share_title?: string
  share_subtitle?: string
  share_image?: string
  kv_image?: string
  name?: string
}

export function useWeChatShare(code: string) {
  async function setup(site: ShareConfig) {
    const wx = (window as any).wx
    if (!wx) return
    try {
      const sign: any = await api.get(`/p/sites/${code}/wechat-signature`, {
        params: { url: window.location.href.split('#')[0] },
      })
      if (!sign.enabled) return
      wx.config({
        debug: false,
        appId: sign.app_id,
        timestamp: sign.timestamp,
        nonceStr: sign.nonce_str,
        signature: sign.signature,
        jsApiList: ['updateAppMessageShareData', 'updateTimelineShareData'],
      })
      const shareData = {
        title: site.share_title || site.name || '微站',
        desc: site.share_subtitle || '',
        link: window.location.href.split('#')[0],
        imgUrl: site.share_image || site.kv_image || '',
      }
      wx.ready(() => {
        wx.updateAppMessageShareData(shareData, () => {})
        wx.updateTimelineShareData({
          title: shareData.title,
          link: shareData.link,
          imgUrl: shareData.imgUrl,
        }, () => {})
      })
      wx.error((res: any) => {
        console.warn('[wx-share]', res?.errMsg)
      })
    } catch {
      // 签名失败静默处理
    }
  }

  return { setup }
}
