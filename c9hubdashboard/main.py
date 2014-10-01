import sys

def main():
    from c9hubdashboard.html import api
    api.app.run(debug=api.cfg.debug, host=api.cfg.host, port=api.cfg.port)

if __name__ == '__main__':
    main()
