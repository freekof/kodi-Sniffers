import sys
import os
import urllib.parse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import xbmcvfs
import time

# 添加 resources/lib 到 sys.path 以便导入 yt-dlp
addon_dir = xbmcaddon.Addon().getAddonInfo('path')
lib_dir = os.path.join(addon_dir, 'resources', 'lib')
sys.path.append(lib_dir)

import yt_dlp
import remote_server
from history_manager import HistoryManager

# 初始化历史记录管理器
addon_data_path = xbmcvfs.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
history_mgr = HistoryManager(addon_data_path)

def get_video_info(url):
    addon = xbmcaddon.Addon()
    ua = addon.getSetting('user_agent')
    nossl = addon.getSetting('nossl') == 'true'
    cookie_path = addon.getSetting('cookie_path')
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'user_agent': ua,
        'nocheckcertificate': nossl,
    }
    
    if cookie_path and os.path.exists(cookie_path):
        ydl_opts['cookiefile'] = cookie_path
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return info
        except Exception as e:
            xbmcgui.Dialog().notification('Error', str(e), xbmcgui.NOTIFICATION_ERROR)
            return None

def list_resolutions(url):
    info = get_video_info(url)
    if not info:
        return

    title = info.get('title', 'Unknown Video')
    thumbnail = info.get('thumbnail', '')
    formats = info.get('formats', [])

    # 过滤出有分辨率信息的视频流
    video_streams = []
    for f in formats:
        if f.get('vcodec') != 'none' and f.get('url'):
            res = f.get('resolution') or f'{f.get("width")}x{f.get("height")}'
            ext = f.get('ext', 'mp4')
            note = f.get('format_note', '')
            label = f"[{ext.upper()}] {res} - {note}"
            video_streams.append({
                'label': label,
                'url': f['url'],
                'title': title,
                'thumbnail': thumbnail
            })

    if not video_streams:
        xbmcgui.Dialog().notification('Info', 'No playable streams found.', xbmcgui.NOTIFICATION_INFO)
        return

    # 保存到历史记录
    history_mgr.add_record(url, title, thumbnail, video_streams)

    handle = int(sys.argv[1])
    
    # 顶部选项 1: 重新嗅探
    resniff_url = f"{sys.argv[0]}?mode=list&url={urllib.parse.quote(url)}"
    li_resniff = xbmcgui.ListItem(label="[COLOR orange]↻ 重新嗅探 / Re-sniff[/COLOR]")
    xbmcplugin.addDirectoryItem(handle=handle, url=resniff_url, listitem=li_resniff, isFolder=True)
    
    # 顶部选项 2: 在浏览器中打开 (处理人机验证)
    li_browser = xbmcgui.ListItem(label="[COLOR lightblue]🌐 在浏览器中打开 / Open in Browser[/COLOR]")
    browser_url = f"{sys.argv[0]}?mode=open_browser&url={urllib.parse.quote(url)}"
    xbmcplugin.addDirectoryItem(handle=handle, url=browser_url, listitem=li_browser, isFolder=False)

    for stream in video_streams:
        li = xbmcgui.ListItem(label=stream['label'])
        li.setArt({'thumb': stream['thumbnail'], 'icon': stream['thumbnail']})
        try:
            li.setInfo('video', {'title': stream['title']})
        except:
            pass
        li.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle=handle, url=stream['url'], listitem=li, isFolder=False)

    xbmcplugin.endOfDirectory(handle)

def play_direct_url(url):
    xbmc.Player().play(url)

def main():
    handle = int(sys.argv[1])
    url_args = urllib.parse.parse_qs(sys.argv[2][1:])
    mode = url_args.get('mode', [None])[0]

    if mode is None:
        base_url = sys.argv[0]
        li_manual = xbmcgui.ListItem(label="[COLOR yellow]手动输入网址 / Manual Input URL[/COLOR]")
        xbmcplugin.addDirectoryItem(handle=handle, url=f"{base_url}?mode=input", listitem=li_manual, isFolder=True)
        
        li_remote = xbmcgui.ListItem(label="[COLOR green]手机远程输入 / Mobile Remote Input[/COLOR]")
        xbmcplugin.addDirectoryItem(handle=handle, url=f"{base_url}?mode=remote", listitem=li_remote, isFolder=True)
        
        li_history = xbmcgui.ListItem(label="[COLOR cyan]最近嗅探记录 / Recent Records[/COLOR]")
        xbmcplugin.addDirectoryItem(handle=handle, url=f"{base_url}?mode=history", listitem=li_history, isFolder=True)
        xbmcplugin.endOfDirectory(handle)
        
    elif mode == 'input':
        keyboard = xbmcgui.Dialog().input('请输入视频网页地址', type=xbmcgui.INPUT_ALPHANUM)
        if keyboard:
            list_resolutions(keyboard)
            
    elif mode == 'remote':
        server_url = remote_server.start_server(history_provider_func=history_mgr.get_records)
        xbmcgui.Dialog().ok('手机远程输入', f'请在手机浏览器访问：\n{server_url}')
        dialog = xbmcgui.DialogProgress()
        dialog.create('等待提交', '请在手机上输入 URL 并点击发送...')
        try:
            while not dialog.iscanceled():
                action = remote_server.get_received_action()
                if action:
                    dialog.close()
                    remote_server.stop_server()
                    if action.get('type') == 'play':
                        play_direct_url(action.get('url'))
                    else:
                        list_resolutions(action.get('url'))
                    return
                time.sleep(1)
        finally:
            dialog.close()
            remote_server.stop_server()
            
    elif mode == 'history':
        records = history_mgr.get_records()
        li_clear = xbmcgui.ListItem(label="[COLOR red]清除所有记录 / Clear All History[/COLOR]")
        xbmcplugin.addDirectoryItem(handle=handle, url=f"{sys.argv[0]}?mode=clear_all_history", listitem=li_clear, isFolder=False)
        
        if records:
            for i, record in enumerate(records):
                li = xbmcgui.ListItem(label=record['title'])
                li.setArt({'thumb': record['thumbnail'], 'icon': record['thumbnail']})
                url = f"{sys.argv[0]}?mode=history_detail&index={i}"
                resniff_url = f"{sys.argv[0]}?mode=list&url={urllib.parse.quote(record['url'])}"
                li.addContextMenuItems([
                    ('重新嗅探 (Re-sniff)', f'Container.Update({resniff_url})'),
                    ('清除此记录 (Delete)', f'RunPlugin({sys.argv[0]}?mode=delete_history&index={i})')
                ])
                xbmcplugin.addDirectoryItem(handle=handle, url=url, listitem=li, isFolder=True)
        xbmcplugin.endOfDirectory(handle)
        
    elif mode == 'clear_all_history':
        if xbmcgui.Dialog().yesno('确认', '是否清除所有嗅探记录？'):
            history_mgr.clear_history()
            xbmc.executebuiltin('Container.Refresh')
        
    elif mode == 'delete_history':
        index = int(url_args.get('index')[0])
        records = history_mgr.get_records()
        if index < len(records):
            records.pop(index)
            history_mgr._save_history(records)
            xbmc.executebuiltin('Container.Refresh')
            
    elif mode == 'open_browser':
        target_url = url_args.get('url')[0]
        xbmc.executebuiltin(f'System.BrowseUrl("{target_url}")')
        
    elif mode == 'history_detail':
        index = int(url_args.get('index')[0])
        records = history_mgr.get_records()
        if index < len(records):
            record = records[index]
            resniff_url = f"{sys.argv[0]}?mode=list&url={urllib.parse.quote(record['url'])}"
            li_resniff = xbmcgui.ListItem(label="[COLOR orange]↻ 重新嗅探 / Re-sniff[/COLOR]")
            xbmcplugin.addDirectoryItem(handle=handle, url=resniff_url, listitem=li_resniff, isFolder=True)
            
            li_browser = xbmcgui.ListItem(label="[COLOR lightblue]🌐 在浏览器中打开 / Open in Browser[/COLOR]")
            browser_url = f"{sys.argv[0]}?mode=open_browser&url={urllib.parse.quote(record['url'])}"
            xbmcplugin.addDirectoryItem(handle=handle, url=browser_url, listitem=li_browser, isFolder=False)

            for stream in record['streams']:
                li = xbmcgui.ListItem(label=stream['label'])
                li.setArt({'thumb': record['thumbnail'], 'icon': record['thumbnail']})
                try:
                    li.setInfo('video', {'title': record['title']})
                except:
                    pass
                li.setProperty('IsPlayable', 'true')
                xbmcplugin.addDirectoryItem(handle=handle, url=stream['url'], listitem=li, isFolder=False)
            xbmcplugin.endOfDirectory(handle)

    elif mode == 'list':
        target_url = url_args.get('url')[0]
        list_resolutions(target_url)

if __name__ == '__main__':
    main()
