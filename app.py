from flask import Flask, jsonify, request, Response
import requests
from flask_mysqldb import MySQL
import msgpack
from flasgger import Swagger

app = Flask(__name__)

# mysql config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'


app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'trpl_movies'
mysql = MySQL(app)
Swagger(app)

@app.route('/')
def root():
    return 'halo dunia'

@app.route('/list-film')
def film():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM film_tayang")

    column_names = [i[0] for i in cursor.description]

    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(column_names, row)))

    return jsonify(data)

    cursor.close()

@app.route('/read')
def seefilm():
    """Routes for module get list films"""
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM film_tayang")

    column_names = [i[0] for i in cursor.description]

    data = []
    for row in cursor.fetchall():
        data.append(dict(zip(column_names, row)))

    return jsonify(data)

    cursor.close()

@app.route('/film/see', methods=['GET', 'POST'])
def list():
    if request.method == 'GET':
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM film_tayang")

        column_names = [i[0] for i in cursor.description]
        
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))

        return jsonify(data)

        cursor.close()
    
    elif request.method == 'POST':
        # GET DATA FROM REQUEST
        nama = request.json['nama_film']
        rate = request.json['rate']
        genre = request.json['genre']

        cursor = mysql.connection.cursor()
        sql = "INSERT INTO film_tayang (nama_film, rate, genre) VALUES (%s, %s, %s)"
        val = (nama,rate,genre)
        cursor.execute(sql,val)

        mysql.connection.commit()

        return jsonify({'message': 'data added succesfully'})
        cursor.close()

@app.route('/read-msgpack', methods=['GET'])
def list_films():
    # Membuka cursor
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT * FROM film_tayang")

        # Mendapatkan nama kolom dari hasil query
        column_names = [i[0] for i in cursor.description]

        # Menyiapkan data sebagai list of dict
        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))

        # Packing data dengan MessagePack
        msgpack_data = msgpack.packb({"message": "OK", "datas": data})

        # Mengembalikan response MessagePack
        return Response(msgpack_data, content_type='application/x-msgpack', status=200)
    finally:
        # Menutup cursor dalam blok finally agar selalu ditutup
        cursor.close()

    # Jika terjadi kesalahan di luar kontrol, mengembalikan respons error default
    error_data = msgpack.packb({"message": "ERROR", "datas": []})
    return Response(error_data, content_type='application/x-msgpack', status=500)

@app.route('/detailfilm')
def detailfilm():
    if 'id_film' in request.args:
        cursor = mysql.connection.cursor()
        sql = "SELECT * FROM film_tayang WHERE id_film = %s"
        val = (request.args['id_film'],)
        cursor.execute(sql, val)

        column_names = [i[0] for i in cursor.description]

        data = []
        for row in cursor.fetchall():
            data.append(dict(zip(column_names, row)))
        
        return jsonify(data)
        cursor.close()

@app.route('/delete-film', methods=['DELETE'])
def deletefilm():
    if 'id_film' in request.args:
        cursor = mysql.connection.cursor()
        sql = "DELETE FROM film_tayang WHERE id_film = %s"
        val = (request.args['id_film'],)
        cursor.execute(sql, val)

        mysql.connection.commit()

        return jsonify({'message':'data deleted succesfully'})
        cursor.close()

@app.route('/edit-film', methods=['PUT'])
def editfilm():
    if 'id_film' in request.args:
        data = request.get_json()

        cursor = mysql.connection.cursor()
        sql = "UPDATE film_tayang SET nama_film=%s, rate=%s, genre=%s WHERE id_film = %s"
        val = (data['nama_film'], data['rate'], data['genre'], request.args['id_film'],)
        cursor.execute(sql, val)

        mysql.connection.commit()
        return jsonify({'message': 'Data updated succesfully'})
        cursor.close()
        


import msgpack
import requests
from flask import Flask, jsonify, request

@app.route('/search-film', methods=['GET'])
def search_film():
    # Mendapatkan parameter pencarian dari query string
    search_query = request.args.get('search', '')
    
    if not search_query:
        return jsonify({"message": "Please provide a search query."}), 400
    
    # Membuka koneksi ke database untuk mencari film
    cursor = mysql.connection.cursor()
    
    # Query untuk mencari film berdasarkan nama atau genre
    sql = """
        SELECT * FROM film_tayang 
        WHERE nama_film LIKE %s OR genre LIKE %s
    """
    like_query = f"%{search_query}%"
    cursor.execute(sql, (like_query, like_query))
    
    column_names = [i[0] for i in cursor.description]
    films = []
    
    for row in cursor.fetchall():
        films.append(dict(zip(column_names, row)))
    
    # Menutup cursor setelah query
    cursor.close()
    
    # Jika tidak ada film yang ditemukan, kembalikan respons kosong
    if not films:
        return jsonify({"message": "No films found matching the search query."}), 404
    
    # Ambil review untuk setiap film dari API reviews
    for film in films:
        film_id = film['id_film']
        try:
            # Mengambil review berdasarkan film_id dengan format msgpack
            response = requests.get(f'http://localhost:5001/api/reviews/film/{film_id}')
            
            # Jika request ke API reviews berhasil, cek format msgpack
            if response.status_code == 200:
                # Menggunakan msgpack untuk mendekodekan data
                review_data = msgpack.unpackb(response.content)
                
                # Jika response berhasil, tambahkan review ke data film
                film['reviews'] = review_data.get('reviews', [])
            else:
                film['reviews'] = []
        except Exception as e:
            # Jika ada error dalam pengambilan review, set review ke list kosong
            film['reviews'] = []
    
    # Mengembalikan hasil pencarian dengan film dan review
    return jsonify({
        "message": "Films found",
        "films": films
    })



if __name__ == '__main__':
    app.run(debug=True)
