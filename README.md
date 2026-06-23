# Coffee-Data-Collection

💡 **「About」**

Coffee Data Collection is based on Django Vue3 Admin

## framework introduction

💡 [django-vue3-admin](https://gitee.com/huge-dream/django-vue3-admin.git) Is a set of all open source rapid development platform, no reservation for individuals and enterprises free use.

* 🧑‍🤝‍🧑Front-end adoption Vue3+TS+pinia+fastcrud。
* 👭The backend uses the Python language Django framework as well as the powerful[Django REST Framework](https://pypi.org/project/djangorestframework)。
* 👫Permission authentication use[Django REST Framework SimpleJWT](https://pypi.org/project/djangorestframework-simplejwt)，Supports the multi-terminal authentication system.
* 👬Support loading dynamic permission menu, multi - way easy permission control.
* 👬Enhanced Column Permission Control, with granularity down to each column.
* 💏Special thanks: [vue-next-admin](https://lyt-top.gitee.io/vue-next-admin-doc-preview/).
* 💡Special thanks:[jetbrains](https://www.jetbrains.com/) To provide a free IntelliJ IDEA license for this open source project.

## Online experience

👩‍👧‍👦👩‍👧‍👦 demo address:[https://demo.dvadmin.com](https://demo.dvadmin.com)

* demo account：superadmin

* demo password：admin123456

👩‍👦‍👦docs:[https://django-vue-admin.com](https://django-vue-admin.com)

## communication

* Communication community:[click here](https://bbs.django-vue-admin.com)👩‍👦‍👦

* plugins market:[click here](https://bbs.django-vue-admin.com/plugMarket.html)👩‍👦‍👦

## source code url:

gitee(Main push)：[https://gitee.com/huge-dream/django-vue3-admin](https://gitee.com/huge-dream/django-vue3-admin)👩‍👦‍👦

github：[https://github.com/huge-dream/django-vue3-admin](https://github.com/huge-dream/django-vue3-admin)👩‍👦‍👦

## core function

1. 👨‍⚕️Menu Management: Configure system menus, operation permissions, button permission flags, backend interface permissions, etc.
2. 🧑‍⚕️Department Management: Configure system organizational structure (company, department, role).
3. 👩‍⚕️Role Management: Role menu permission assignment, data permission assignment, set role-based data scope permissions by department.
4. 🧑‍🎓Button Permission Control: Authorize role-specific button permissions and interface permissions, enabling authorization of data scope for each interface.
5. 🧑‍🎓Field Column Permission Control: Authorize page field display permissions, specifically for the display permissions of a certain column.
6. 👨‍🎓User Management: Users are system operators, and this function is mainly used for system user configuration.
7. 👬API Whitelist: Configure interfaces that do not require permission verification.
8. 🧑‍🔧Dictionary Management: Maintain frequently used and relatively fixed data in the system.
9. 🧑‍🔧Region Management: Manage provinces, cities, counties, and districts.
10. 📁File Management: Unified management of all files, images, etc., on the platform.
11. 🗓️Operation Logs: Record and query logs for normal system operations and exceptional system information.
12. 🔌[Plugin Market](https://bbs.django-vue-admin.com/plugMarket.html): Applications and plugins developed based on the Django-Vue-Admin framework.

## plugins market 🔌

Updating...

## Repository Branch Explanation 💈
Main Branch: master (stable version)
Development Branch: develop

## before start project you need:

~~~
Python >= 3.11.0 (Minimum version 3.9+)
Node.js >= 16.0
Mysql >= 8.0 (Optional, default database: SQLite3, supports 5.7+, recommended version: 8.0)
Redis (Optional, latest version)
~~~

## frontend♝

```bash
# clone code
git clone https://gitee.com/huge-dream/django-vue3-admin.git

# enter code dir
cd web

# install dependence
npm install yarn
yarn install --registry=https://registry.npm.taobao.org

# Start service
yarn run dev
# Visit http://localhost:8080 in your browser
# Parameters such as boot port can be configured in the #.env.development file
# Build the production environment
# yarn run build
```

## backend💈

~~~bash
1. enter code dir cd backend
2. copy ./conf/env.example.py to ./conf dir，rename as env.py
3. in env.py configure database information
 mysql database recommended version: 8.0
 mysql database character set: utf8mb4
4. install pip dependence
 pip3 install -r requirements.txt
5. Execute the migration command:
 python3 manage.py makemigrations
 python3 manage.py migrate
6. Initialization data
 python3 manage.py init
7. Initialize provincial, municipal and county data:
 python3 manage.py init_area
8. start backend
 python3 manage.py runserver 0.0.0.0:8000
or uvicorn :
  uvicorn application.asgi:application --port 8000 --host 0.0.0.0 --workers 8
~~~

### visit backend swagger

* visit url：[http://localhost:8080](http://localhost:8080) (The default address is this one. If you want to change it, follow the configuration file)
* account：`superadmin` password：`admin123456`

### docker-compose

~~~shell
docker-compose up -d
# Initialize backend data (first execution only)
docker exec -ti dvadmin3-django bash
python manage.py makemigrations 
python manage.py migrate
python manage.py init_area
python manage.py init
exit

frontend url：http://127.0.0.1:8080
backend url：http://127.0.0.1:8080/api
# Change 127.0.0.1 to your own public ip address on the server
account：`superadmin` password：`admin123456`

# docker-compose stop
docker-compose down
#  docker-compose restart
docker-compose restart
#  docker-compose on start build
docker-compose up -d --build
~~~

## Demo screenshot✅

![image-01](https://foruda.gitee.com/images/1701348994587355489/1bc749e7_5074988.png)

![image-02](https://foruda.gitee.com/images/1701349037811908960/80d361db_5074988.png)

![image-03](https://foruda.gitee.com/images/1701349224478845203/954f0a7b_5074988.png)

![image-04](https://foruda.gitee.com/images/1701349248928658877/64926724_5074988.png)

![image-05](https://foruda.gitee.com/images/1701349259068943299/1306ba40_5074988.png)

![image-06](https://foruda.gitee.com/images/1701349294894429495/e3b3a8cf_5074988.png)

![image-07](https://foruda.gitee.com/images/1701350432536247561/3b26685e_5074988.png)

![image-08](https://foruda.gitee.com/images/1701350455264771992/b364c57f_5074988.png)

![image-09](https://foruda.gitee.com/images/1701350479266000753/e4e4f7c5_5074988.png)

![image-10](https://foruda.gitee.com/images/1701350501421625746/f8dd215e_5074988.png)


