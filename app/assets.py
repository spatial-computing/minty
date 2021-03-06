from flask_assets import Bundle

def create_assets(assets):

    css = Bundle(
        'css/main.css',
        filters='cssmin',
        output='bundle/main.min.css'
    )
    assets.register('CSS_FRAMEWORKS', css)

    js = Bundle(
        'js/bash.js',
        filters='jsmin', 
        output='bundle/bash.min.js'
    )
    assets.register('JS_FRAMEWORS_BASH', js)
    
    js = Bundle(
        'js/viztype.js',
        filters='jsmin', 
        output='bundle/viztype.min.js'
    )
    assets.register('JS_FRAMEWORS_VIZTYPE', js)