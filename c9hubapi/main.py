import sys

def main():
    from c9hubapi.rest import api
    api.app.run(debug=True, host='0.0.0.0', port=3232)

if __name__ == '__main__':
    main()
