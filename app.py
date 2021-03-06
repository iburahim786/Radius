from flask import Flask, render_template, flash, url_for, request, redirect
import os
import linecache
import subprocess

app = Flask(__name__)

# Add sql secret key
app.secret_key = 'novell@123'


# Home Page
@app.route('/')
def home():
    return render_template('home.html')


# About Page
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contactus')
def contactus():
    return render_template('contact_us.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    # cur = mysql.connection.cursor()
    # cur.session.rollback()
    return render_template('500.html'), 500


# Radius ###############################################################################################################

@app.route('/rusers', methods=['GET', 'POST'])
def radius_users():
    final_lineList = []
    # with open('/etc/raddb/users') as f:
    with open('/etc/freeradius/3.0/users') as f:
        lineList = f.readlines()
        for line in lineList:
            if 'Cleartext-Password' in line and '#' not in line[0]:
                final_lineList.append(line.replace("\n", ""))
    return render_template('rusers.html', flists=final_lineList)


@app.route('/add_ruser', methods=['GET', 'POST'])
def add_ruser():
    if request.method == 'POST':
        ruser = request.form['ruser']
        rpassword = request.form['rusrpwd']
        with open("/etc/freeradius/3.0/users", "r") as fr:
            lines = fr.readlines()
            for line in lines:
                if ruser in line:
                    flash("User already exists!, Please add different user", 'danger')
                    return redirect(url_for('radius_users'))
        with open("/etc/freeradius/3.0/users", "w") as fw:
            fw.seek(0)
            fw.write(ruser + ' Cleartext-Password := "' + rpassword + '"\n')
            for line in lines:
                fw.write(line)
        flash("User added successfully!, Please restart the service", 'success')
        # return redirect(url_for('radius_users'))
    return redirect(url_for('radius_users'))


@app.route('/delete_ruser/<string:ruser>', methods=['GET', 'POST'])
def delete_ruser(ruser):
    with open("/etc/freeradius/3.0/users", "r") as f:
        lines = f.readlines()
    with open("/etc/freeradius/3.0/users", "w") as f:
        for line in lines:
            if ruser not in line:
                f.write(line)
    flash("User deleted successfully!, Please restart the service", 'success')
    return redirect(url_for('radius_users'))


@app.route('/rclients', methods=['GET', 'POST'])
def radius_clients():
    final_client_list = []
    with open('/etc/freeradius/3.0/clients.conf', 'r') as fr:
        read_lines = fr.readlines()
    with open('/etc/freeradius/3.0/clients.conf') as f:
        for num, line in enumerate(f, 1):
            if 'client' in line and '#' not in line:
                client_line_split = line.split()
                ip_line = read_lines[num]
                sec_line = read_lines[num + 1]
                if 'secret' in sec_line and 'ipaddr' in ip_line and '#' not in sec_line:
                    secret_line_split = sec_line.split()
                    final_str = client_line_split[1].replace("{", "") + " " + secret_line_split[2]
                    final_client_list.append(final_str)
    return render_template('rclients.html', flists=final_client_list)


@app.route('/add_rclient', methods=['GET', 'POST'])
def add_rclient():
    if request.method == 'POST':
        rclient = request.form['rclient']
        rclientpaswd = request.form['rclntpwd']
        with open("/etc/freeradius/3.0/clients.conf", "r") as fr:
            lines = fr.readlines()
            for line in lines:
                if rclient in line:
                    flash("Client already exists!, Please add different Client", 'danger')
                    return redirect(url_for('radius_clients'))
        with open('/etc/freeradius/3.0/clients.conf') as f:
            for num, line in enumerate(f, 1):
                continue
        with open("/etc/freeradius/3.0/clients.conf", "a") as fw:
            fw.seek(num)
            fw.write('\nclient ' + rclient + ' {\n  ipaddr = ' + rclient + '\n  secret = ' + rclientpaswd + '\n}')
        flash("Client added successfully!, Please restart the service", 'success')
        # return redirect(url_for('radius_users'))
    return redirect(url_for('radius_clients'))


def delete_multiple_lines(original_file, line_numbers):
    """In a file, delete the lines at line number in given list"""
    is_skipped = False
    counter = 0
    # Create name of dummy / temporary file
    dummy_file = original_file + '.bak'
    # Open original file in read only mode and dummy file in write mode
    with open(original_file, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        # Line by line copy data from original file to dummy file
        for line in read_obj:
            # If current line number exist in list then skip copying that line
            if counter not in line_numbers:
                write_obj.write(line)
            else:
                is_skipped = True
            counter += 1

    # If any line is skipped then rename dummy file as original file
    if is_skipped:
        os.remove(original_file)
        os.rename(dummy_file, original_file)
    else:
        os.remove(dummy_file)


@app.route('/delete_rclient/<string:rclient>', methods=['GET', 'POST'])
def delete_rclient(rclient):
    final_num = 0
    with open('/etc/freeradius/3.0/clients.conf', 'r') as f:
        for num, line in enumerate(f, 1):
            if rclient in line and '#' not in line:
                final_num = num
                break
    # ip_line = linecache.getline('/etc/freeradius/3.0/clients.conf', final_num + 1)
    # sec_line = linecache.getline('/etc/freeradius/3.0/clients.conf', final_num + 2)
    f = open('/etc/freeradius/3.0/clients.conf')
    flines = f.readlines()
    ip_line_del = flines[final_num]
    sec_line_del = flines[final_num + 1]
    if 'secret' in sec_line_del and 'ipaddr' in ip_line_del and '#' not in sec_line_del:
        delete_multiple_lines('/etc/freeradius/3.0/clients.conf',
                              [final_num - 1, final_num, final_num + 1, final_num + 2])
        flash("Client deleted successfully!, Please restart the service", 'success')
    else:
        flash("Default format is not matching to delete, Please check manually", 'danger')
    return redirect(url_for('radius_clients'))


@app.route('/rservice', methods=['GET', 'POST'])
def radius_service():
    subprocess.call(['> /home/iburahim/Radius/radius.txt'], shell=True)
    subprocess.call(['sudo systemctl status freeradius.service > /home/iburahim/Radius/radius.txt'], shell=True)
    f = open('/home/iburahim/Radius/radius.txt', 'r')
    maven = f.readlines()
    return render_template('rservice.html', filecontent=maven)


@app.route('/rservice/<string:status>', methods=['GET', 'POST'])
def rservice_status(status):
    code = subprocess.call(['systemctl ' + status+ ' freeradius.service'], shell=True)
    if code == 0:
        if status == 'stop':
            flash("Radius service successfully " + status + "ped", 'success')
        else:
            flash("Radius service successfully " + status + "ed", 'success')
    else:
        flash('Failure to execute the service command: ' + status + ' and ' + str(code), 'danger')
    return redirect(url_for('radius_service'))


if __name__ == '__main__':
    app.run(debug=True)
