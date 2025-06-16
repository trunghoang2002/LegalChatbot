from server_stream import app

# for linux
if __name__ == "__main__":
    app.run()

# # for windows
# from waitress import serve

# if __name__ == "__main__":
#     print("Starting production server on http://0.0.0.0:5000")
#     serve(app, host='0.0.0.0', port=5000, threads=4)