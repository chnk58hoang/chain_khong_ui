from nicegui import ui, app
import requests
import os


FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSfcRAt79uDrsDPHEc-9yrDdR6XGPJiuqo5PIUe2Oy4fUiI5MA/viewform?pli=1'



# ------------------ CSS cho đĩa than ------------------
ui.add_head_html("""
<script>
    // chạy ngay khi browser load lại trang
    localStorage.clear();
    sessionStorage.clear();
</script>
<style>
.vinyl-disc {
    width: 50vmin;       /* chiều rộng = 50% của chiều nhỏ nhất màn hình (width hoặc height) */
    height: 50vmin;      /* giữ tỉ lệ 1:1 */
    max-width: 500px;    /* giới hạn tối đa */
    max-height: 500px;
    border-radius: 50%;
    background: radial-gradient(circle at 50% 50%, #000 60%, #222 100%);
    box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    margin-bottom: 2vh;
    display: flex;
    justify-content: center;
    align-items: center;
    position: relative;
}

.vinyl-disc .center {
    width: 8%;
    aspect-ratio: 1;
    border-radius: 50%;
    background: #888;
    z-index: 2;
}

.vinyl-disc img {
    width: 90%;
    height: 90%;
    border-radius: 50%;
    position: absolute;
    z-index: 3;
}
.record-overlay {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    pointer-events: none;
    z-index: 5;
}
.spin {
    animation: spin 4s linear infinite;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
""")

# ------------------ Biến trạng thái ------------------
state = {'spinning': False, 'audio_playing': False}

# ------------------ UI chính ------------------
with ui.row().style('width:100%;height:100vh;gap:10px;align-items: stretch;'):

    # Sidebar trái: search nhạc Spotify
    with ui.column().style(
        '''
        width:33%;
        min-height:100vh;
        padding:25px;
        background: linear-gradient(145deg,#3b5998,#8b9dc3);
        color:white;
        border-radius:20px;
        '''
    ):
        ui.image('images/chainkhonglogo-05_1.png').style('''
            width: 70%;
            height: auto;
            position: relative;
        ''')
        ui.image('images/chainkhongpickyourvibe-05.png').style('''
            width: 50%;
            max-width: 400px;
            height: auto;
            position: relative;
            transform: translateX(20%);                                                                            
        ''')
        with ui.input('', placeholder='Pick your vibe ...') as search_input:
            ui.icon('search').style('color: #b3b3b3; margin-left: 8px;') \
                .props('size=18px') \
                .on('click', lambda: print('Search clicked!'))
        search_input \
            .style('''
                border-radius: 100px;   /* pill shape */
                border: none;
                background: white;
                color: black;
                font-size: 14px;
                padding: 10px 16px 10px 36px; /* chừa chỗ cho icon */
                width: 100%;
                box-shadow: none;
                transition: background 0.3s ease;
            ''') \
            .classes('focus:outline-none') \
            .props('clearable')


        results_container = ui.column().style(
        '''
        margin-top: 10px;
        gap: 0px;
        width: 100%;
        overflow-y: auto;
        '''
    )
        track_container = ui.column()

    # Center: đĩa than + music player
    with ui.column().style(
        '''
        width:33%;
        min-height:100vh;
        align-items:center;
        padding:25px;
        background: linear-gradient(145deg,#3b5998,#8b9dc3);
        border-radius:20px;
        box-shadow:0 10px 20px rgba(0,0,0,0.1);
        '''
    ):
        record_div = ui.html('''
            <div class="vinyl-disc">
                <div class="center"></div>
                <img id="discImage" src="" style="display:none;">
            </div>
        ''')

        song_title_label = ui.label('').style('font-weight:bold;font-size:20px; text-align:center;')
        artist_label = ui.label('').style('color:white;font-size:18px; text-align:center;')
        with ui.card().style(
            '''
            width:90%;
            padding:40px 20px;
            border-radius:20px;
            box-shadow:0 5px 15px rgba(0,0,0,0.1);
            background-size: cover;
            background-position: center;
            display:flex;
            flex-direction:column;
            align-items:center;
            position:relative;
            color:white;
            text-shadow: 0 0 5px rgba(0,0,0,0.7);
        '''
        ):
            album_cover_img = ui.image('').style(
                '''
                width:40%;
                max-width:120px;
                height:auto;
                margin-bottom:15px;
                z-index:1;
                '''
            )

            ui.image('images/chainkhongmascot-02.png').style(
                '''
                width:50%;       /* có thể thay đổi % cho responsive */
                height:auto;
                position:absolute;
                top:0;
                left:0;
                transform: rotate(-10deg) translate(-20%, -50%);
                border-radius:50%;
                '''
            )

            with ui.row().style('justify-content:center;align-items:center;margin-top:10px;gap:20px;width:100%;'):
                play_btn = ui.icon('play_arrow').style(
                    'color:white;background-color:#1db954;border-radius:50%;padding:15px;font-size:36px;box-shadow:0 3px 12px rgba(0,0,0,0.2);cursor:pointer;'
                )

                def toggle_spin():
                    js = """
                    let audio = document.getElementById('previewAudio');
                    if (audio) {{
                        if ({playing}) {{
                            audio.pause();
                        }} else {{
                            audio.play();
                        }}
                    }}
                    """.format(playing=state['audio_playing'])
                    
                    if state['audio_playing']:
                        # đang chơi -> pause
                        ui.run_javascript(js)
                        play_btn.props('name=play_arrow')
                        ui.run_javascript('document.querySelector(".vinyl-disc").classList.remove("spin");')
                        state['spinning'] = False
                        state['audio_playing'] = False
                    else:
                        # đang pause -> play
                        ui.run_javascript(js)
                        play_btn.props('name=pause')
                        ui.run_javascript('document.querySelector(".vinyl-disc").classList.add("spin");')
                        state['spinning'] = True
                        state['audio_playing'] = True
                
                def toggle_play():
                    js_code = f"""
                    let audio = document.getElementById('previewAudio');
                    let playBtn = document.querySelector('.play-btn');
                    if (!audio) {{
                        return;
                    }}
                    if (!audio.src) {{
                        // Nếu chưa có bài hát nào được chọn, không làm gì
                        return;
                    }}
                    if (audio.paused) {{
                        console.log(audio.paused);
                        audio.play();
                        playBtn.innerHTML = 'pause';
                    }} else {{
                        console.log('Pausing audio');
                        audio.pause();
                        playBtn.innerHTML = 'play_arrow';
                    }}
                    """
                    ui.run_javascript(js_code)

                play_btn.on('click', toggle_play)
                play_btn.on('click', toggle_spin)

    # Sidebar phải: upload ảnh cá nhân
    with ui.column().style(
        '''
        width:30%;
        min-height:100vh;
        padding:25px;
        background: linear-gradient(145deg,#3b5998,#8b9dc3);
        color:white;
        border-radius:20px;
        '''
    ):
        ui.image('images/chainkhongmaykyuc.png').style('''
            width: 100%;
            max-width: 400px;
            height: auto;
            position: relative;
            margin-bottom: 20px;
        ''')

        ui.html('<input type="file" id="uploadInput" style="display:none;">')

        ui.button('Chọn ảnh', on_click=lambda: ui.run_javascript('document.getElementById("uploadInput").click()')).style(
            '''
            background-color:white;color:#ff6f91;
            border-radius:15px;padding:10px 20px;
            font-weight:bold;cursor:pointer;
            '''
        )

        def setup_upload_js():
            js_code = """
            const input = document.getElementById('uploadInput');
            const discImg = document.getElementById('discImage');
            if (input && discImg) {
                input.onchange = () => {
                    if(input.files.length>0){
                        const file = input.files[0];
                        const reader = new FileReader();
                        reader.onload = e => {
                            discImg.src = e.target.result;
                            discImg.style.display='block';
                        };
                        reader.readAsDataURL(file);
                    }
                };
            }
            """
            ui.run_javascript(js_code)

        ui.timer(0.1, setup_upload_js, once=True)

        image_urls = [os.path.join('collections', img) for img in os.listdir('collections')]
        ui.label('GALLERY').style('margin-top:30px;font-size:18px;font-weight:bold;text-align:center;')
        gallery_grid = ui.grid().classes('grid-cols-2 gap-2 w-full').style(
            '''
            grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
            gap: 10px;
            '''
        )
        for url in image_urls:
            with gallery_grid:
                small_img = ui.image(url).style(
                '''
                width:100%; 
                aspect-ratio:1/1;   
                object-fit:cover;    
                border-radius:5px;
                cursor:pointer;
                '''
            )

            # Khi click vào ảnh nhỏ, mở dialog ảnh lớn
            def show_large_image(e, img_url=url):
                dlg = ui.dialog()  # tạo dialog
                with dlg:
                    ui.image(img_url).style('width:100%;height:auto;')
                    ui.button('Đóng', on_click=lambda: dlg.close())
                dlg.open()  # hiển thị dialog

            small_img.on('click', show_large_image)
        ui.button('ORDER NOW !', on_click=lambda: ui.run_javascript(f'window.open("{FORM_URL}", "_blank")')).style(
            '''
            background-color:white;color:#ff6f91;
            border-radius:15px;padding:10px 20px;
            font-weight:bold;cursor:pointer;
            '''
        )
        ui.image('images/daychuyen.png').style('''
            width: 100%;
            max-width: 400px;
            height: auto;
            position: relative;
            transform: translate(20%, -15%);                                                                                                            
        ''')


def play_song(preview, cover, title, artist):
    # Cập nhật music player
    print(f'Playing: {title} by {artist}')
    print(f'Preview URL: {preview}')
    song_title_label.set_text(title)
    artist_label.set_text(artist)
    song_title_label.update()
    artist_label.update()
    album_cover_img.set_source(cover)
    album_cover_img.update()
    state['audio_playing'] = True
    play_btn.props('name=pause')
    # Chạy JS để cập nhật đĩa và audio
    js_code = f"""
    let audio = document.getElementById('previewAudio');
    if (!audio) {{
        audio = document.createElement('audio');
        audio.id = 'previewAudio';
        document.body.appendChild(audio);
    }}
    audio.src = '{preview}';
    console.log(audio.paused);
    audio.play();
    console.log(audio.paused);
    document.querySelector('.vinyl-disc').classList.add('spin');
    """
    ui.run_javascript(js_code)


def search_songs():
    query = search_input.value
    if not query:
        return
    results_container.clear()
    url = f'https://api.deezer.com/search?q={query}&limit=10'
    res = requests.get(url)
    if res.status_code == 200:
        data = res.json()
        for song in data['data']:
            title = song['title']
            print(f'Title: {title}')
            artist = song['artist']['name']
            album_cover = song['album']['cover_medium']
            preview = song['preview']

            with results_container:
                with ui.row().style('align-items: center; gap: 10px; cursor: pointer;').on('click', lambda preview=preview, cover=album_cover, title=title, artist=artist: play_song(preview, cover, title, artist)):
                    ui.image(album_cover).style('width:50px; height:50px; border-radius:5px;')
                    with ui.column():
                        ui.label(title).style('font-weight:bold; font-size:14px;')
                        ui.label(artist).style('color:gray; font-size:12px;')
                    # Nút play preview + update ảnh đĩa
                    # ui.button('▶️', on_click=lambda preview=preview, cover=album_cover, title=title, artist=artist: play_song(preview, cover, title, artist))

@app.on_connect
def reset_session(client):
    # clear search + nhạc (như đã bàn ở trên)
    search_input.set_value('')
    results_container.clear()
    song_title_label.set_text('')
    artist_label.set_text('')
    album_cover_img.set_source('')
    album_cover_img.update()
    # gắn lại upload js cho tab mới
    setup_upload_js()

search_input.on('change', lambda e: search_songs())
ui.run(title='Chain Không')