from lib import create_app

application = create_app('production')

if __name__ == '__main__':
	application.run(debug=False)