from datetime import datetime
from functools import wraps
from flask import render_template, request, redirect, session, url_for, flash
from app import app
from models import AdRequest, Campaign, Influencer, Sponsor,  db, User
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import json
from uuid import uuid4




@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Please fill out all fields')
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('Username does not exists')
        return redirect(url_for('login'))
    
    if not check_password_hash(user.passhash,password):
        flash('Incorrect password')
        return redirect(url_for('login'))
    
    session['user_id'] = user.id

    if user.user_type=='sponsor':
        sponsor = Sponsor.query.filter_by(user_id=user.id).first()
        session['sponsor_id'] = user.id
        if sponsor:
            flash('Login successful')
            return redirect(url_for('sponsor_profile'))
        else:
            return redirect(url_for('sponsor_reg'))
    
    elif user.user_type=='influencer':
        influencer = Influencer.query.filter_by(user_id=user.id).first()
        if influencer:
            flash('Login successful')
            return redirect(url_for('influencer_profile'))
        else:
            return redirect(url_for('influencer_registration'))
    
    elif user.admin:
        flash('Login successful')
        return redirect(url_for('admin_profile'))
    return redirect(url_for('login'))



@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_post():
    username = request.form. get('username')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')
    email = request.form.get('email')
    user_type = request.form.get('user_type')
    admin_key = request.form.get('admin_key')
    admin = False
    is_flagged = False
    
    if not username or not password or not confirm_password or not email or not user_type:
        flash('Please fill out all fields')
        return redirect(url_for('register'))
    
    if password != confirm_password:
        flash('Password do not match')
        return redirect(url_for('register'))
    
    user = User.query.filter_by(username=username).first()

    if user:
        flash('Username already exists')
        return redirect(url_for('register'))
    
    password_hash = generate_password_hash(password)

    if admin_key == 'admin007':
        admin = True

        new_user = User(username=username, passhash=password_hash, email=email, user_type=user_type, admin= admin,is_flagged=is_flagged)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    elif user_type=='influencer' or user_type=='sponsor':
        new_user = User(username=username, passhash=password_hash, email=email, user_type=user_type, is_flagged=is_flagged)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    else:
        flash('Please provide Admin key to register as admin')
        return redirect(url_for('register'))
    
    
#------------decorators-------------------------    
def auth_required(func):
    @wraps(func)
    def inner(*args,**kwargs):
        if 'user_id' in session:
            return func(*args, **kwargs)
        else:
            flash('Please login to continue')
            return redirect(url_for('login'))
    return inner

def admin_req(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

def is_req(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.admin:
            flash('You are not authorized to access this page')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

def influencer_req(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.user_type =='influencer':
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner

def sponsor_req(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to continue')
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if not user.user_type =='sponsor':
            flash('Access Denied')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    return inner


@app.route('/logout')
@auth_required
def logout():
    session.pop('user_id')
    return redirect(url_for('login'))

@app.route('/')
@auth_required
def index():
    user = User.query.get(session['user_id'])
    if 'user_id' in session:
        return render_template('index.html',user=user)
    else:
        flash('Please login to continue')
        return redirect(url_for('login'))

@app.route('/user_update')
@auth_required
def user_update():
    user = User.query.get(session['user_id'])
    return render_template('user_update.html',user=user)

@app.route('/user_update', methods=['POST'])
@auth_required
def user_update_post():
    username = request.form.get('name')
    cpassword = request.form.get('cpassword')
    password = request.form.get('new_password')
    email = request.form.get('email')

    if not username or not cpassword or not password:
        flash('Please fill out all the required fields')
        return redirect(url_for('user_update'))
    
    user = User.query.get(session['user_id'])
    if not check_password_hash(user.passhash, cpassword):
        flash('Incorrect password')
        return redirect(url_for('user_update'))
    
    if username != user.username:
        new_username = User.query.filter_by(username=username).first()
        if new_username:
            flash('Username already exists')
            return redirect(url_for('user_update'))
        
    new_password_hash = generate_password_hash(password)
    user.username = username
    user.passhash = new_password_hash
    user.email = email
    db.session.commit()
    flash('Profile updated successfully')
    
    if user.user_type == 'admin':
        return redirect(url_for('admin_profile'))
    
    if user.user_type == 'sponsor':
        return redirect(url_for('sponsor_profile'))
    
    if user.user_type == 'influencer':
        return redirect(url_for('influencer_profile'))
        




#------------------admin pages--------------------

@app.route('/admin/profile')
@admin_req
def admin_profile():
    user = User.query.get(session['user_id'])
    return render_template('/admin/profile.html', user=user)


@app.route('/admin')
@admin_req
def admin_dashboard():
    user = User.query.get(session['user_id'])
    users = User.query.all()
    total_users = User.query.count()

    user_counts = db.session.query(User.user_type, db.func.count(User.id)).group_by(User.user_type).all()

    labels = [item[0] for item in user_counts]
    data = [item[1] for item in user_counts]
    
    total_influencers = Influencer.query.count()
    total_sponsors = Sponsor.query.count()

    labels1 = ['Influencers', 'Sponsors']
    data1 = [total_influencers, total_sponsors]
    
    return render_template('/admin/dashboard.html',user=user,users=users, user_counts=user_counts, total_users=total_users, labels=labels, data=data,
                           labels1=labels1 , data1=data1)


@app.route('/admin/<int:user_id>/delete')
@admin_req
def delete_user(user_id):
    user = User.query.get(session['user_id'])
    users = User.query.get(user_id)
    if not users:
        flash("User does not exist ")
        return redirect(url_for("admin_dashboard"))
    return render_template("/admin/delete.html", users=users , user=user)




@app.route('/admin/<int:user_id>/delete' , methods=['POST'])
@admin_req
def delete_user_post(user_id):
    users = User.query.get(user_id)
    if not users:
        flash("User does not exist ")
        return redirect(url_for("admin_dashboard"))
    
    db.session.delete(users)
    db.session.commit()

    flash('User Deleted Successfully')
    return redirect(url_for('admin_dashboard'))




        

@app.route('/user/<int:user_id>/info')
def user_info(user_id):
    users = User.query.get(user_id)
    user = User.query.get(session['user_id'])

   
    influencer = Influencer.query.filter_by(user_id=user_id).first()
    sponsor = Sponsor.query.filter_by(user_id=user_id).first()

    if influencer:
        return render_template('/admin/ip.html', influencer=influencer, user=user, users=users)  
    elif sponsor:
        return render_template('/admin/sp.html',sponsor=sponsor, user=user , users = users)
    else:
        flash(" The user is not an active user")
        return redirect(url_for('admin_dashboard')) 




@app.route('/admin/campaign')
@admin_req
def admin_campaign():
    user = User.query.get(session['user_id'])
    sponsors = Sponsor.query.join(Campaign, Sponsor.id == Campaign.sponsor_id).all()
    total_camp = Campaign.query.count()
    pub_camp = Campaign.query.filter_by(visibility='Public').count()
    pvt_camp = Campaign.query.filter_by(visibility= 'Private').count()
     

    labels2 = ['Campaigns' , 'Public' , 'Private']
    data2 = [total_camp , pub_camp , pvt_camp]

    total_adreq = AdRequest.query.count()
    pending_request = AdRequest.query.filter_by(status = 'Pending').count()
    accepted_request = AdRequest.query.filter_by(status = 'Accepted').count()
    declined_request = AdRequest.query.filter_by(status = 'Declined').count()

    labels3 = ['Adrequest','Pending ','Accepted','Declined']
    data3 = [total_adreq, pending_request,accepted_request,declined_request]
    return render_template('/admin/campaign.html',user=user,sponsors=sponsors , labels2=labels2 , data2=data2 ,
                            labels3=labels3, data3=data3)








@app.route('/admin/<int:sponsor_id>/show_campaign')
@admin_req
def admin_show_campaign(sponsor_id):
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.get(sponsor_id)
    campaigns = sponsor.campaigns

    if not sponsor:
        flash("Sponsor Does Not Exist")
        return redirect(url_for("admin_campaign"))

    return render_template("/admin/show.html", sponsor=sponsor , user=user, campaigns=campaigns)

@app.route('/admin/<int:campaign_id>/view')
@admin_req
def admin_view(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    request = AdRequest.query.filter_by(campaign=campaign).all()
    
    if not request:
        flash ("No Request Till Now")

    return render_template('/admin/view.html', campaign=campaign, request=request, user=user)


@app.route('/admin/flag_user/<int:user_id>', methods=['GET', 'POST'])
@admin_req
def admin_flag_user(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        user.is_flagged = not user.is_flagged  
        db.session.commit()
        flash(f"User '{user.username}' has been {'flagged' if user.is_flagged else 'unflagged'} successfully!", 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('/admin/flag_user.html', user=user)


@app.route('/admin/flag_campaign/<int:campaign_id>', methods=['GET', 'POST'])
@admin_req  
def admin_flag_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    user = User.query.get(session['user_id'])

    if request.method == 'POST':
        campaign.is_flagged = not campaign.is_flagged  
        db.session.commit()
        flash(f"Campaign '{campaign.name}' has been {'flagged' if campaign.is_flagged else 'unflagged'} successfully!", 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('/admin/flag_campaign.html', campaign=campaign, user=user)


#-------------------------------------------------#

#------------------sponsor_pages-------------------#
@app.route('/sponsor/sp_reg')
@sponsor_req
def sponsor_reg():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return render_template('sponsor/sp_reg.html', user=user)
    
@app.route('/sponsor/sp_reg', methods=['POST'])
@sponsor_req
def sponsor_registration_post():
    user = User.query.get(session['user_id'])
    cname = request.form.get('cname')
    industry = request.form.get('industry')
    budget = request.form.get('budget')

    new_sponsor = Sponsor(user_id=user.id,company_name=cname , industry=industry , budget=budget)
    db.session.add(new_sponsor)
    db.session.commit()
    session['sponsor_id'] = new_sponsor.id
    return redirect(url_for('sponsor_profile'))

@app.route('/sponsor/profile')
@sponsor_req
def sponsor_profile():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    flag = user.is_flagged
    
    if not flag:
        if sponsor:
            return render_template('/sponsor/profile.html', sponsor=sponsor,user=user) 
        else:
            flash("Continue registration")
            return redirect(url_for('sponsor_reg'))
    else:
        flash("You have been flagged  by admin")
        return render_template('/sponsor/profile.html', sponsor=sponsor,user=user) 



#-----------------------------__-------------------------------

#---------------------------------------------------


@app.route('/sponsor/s_update')
@sponsor_req
def sponsor_update():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    return render_template('/sponsor/s_update.html', user=user, sponsor=sponsor)


@app.route('/sponsor/s_update', methods=['POST'])
@sponsor_req
def sponsor_update_post():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    cname = request.form.get('cname')
    industry = request.form.get('industry')
    budget = request.form.get('budget')

    sponsor.company_name  = cname
    sponsor.industry = industry
    sponsor.budget = budget
    
    db.session.commit()
    flash('Profile updated successfully')
    return redirect(url_for('sponsor_profile'))
 


@app.route('/sponsor')
@sponsor_req
def sponsor_home():
    user = User.query.get(session['user_id'])
    flag = user.is_flagged
    
    if not flag:
        sponsor = Sponsor.query.filter_by(user_id=user.id).first()
        if sponsor:
            campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()
            return render_template('/sponsor/home.html',user=user, campaigns=campaigns)
        else:
            flash("Continue registration")
            return redirect(url_for('sponsor_reg'))
    else:
        return redirect(url_for('sponsor_profile'))


    


@app.route('/sponsor/create')
@sponsor_req
def campaign_create():
    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    return render_template('/sponsor/create.html',user=user)

@app.route('/sponsor/create', methods=['POST'])
@sponsor_req  
def create_campaign_post():
    name = request.form.get('name')
    description = request.form.get('description')
    niche = request.form.get('niche')
    start_date = request.form.get('start_date')  
    end_date = request.form.get('end_date')  
    budget = request.form.get('budget')  
    visibility = request.form.get('visibility')
    goals = request.form.get('goals')

    user = User.query.get(session['user_id'])
    sponsor = Sponsor.query.filter_by(user_id=user.id).first()
    is_flagged = False

    sponsor_id = sponsor.id

    

    if not name or not description or not niche or not start_date or not end_date or not budget or not visibility or not goals:
        flash('Please fill all the fields')
        return redirect(url_for('campaign_create'))


    new_campaign = Campaign(sponsor_id=sponsor_id,name=name,description=description,niche=niche,
                            start_date=datetime.strptime(start_date, '%Y-%m-%d'), 
                            end_date=datetime.strptime(end_date, '%Y-%m-%d'),
                             budget=budget, visibility=visibility,goals=goals, is_flagged=is_flagged)
    db.session.add(new_campaign)
    db.session.commit()
    flash('Campaign Added Successfully')
    return redirect(url_for('sponsor_home'))


@app.route('/campaign/<int:campaign_id>/edit')
@sponsor_req
def edit_campaign(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        flash("Campaign Does Not Exist")
        return redirect(url_for("sponsor_home"))
    return render_template("/campaign/edit.html", campaign=campaign , user=user)



@app.route('/campaign/<int:campaign_id>/edit', methods=['POST'])
@sponsor_req
def edit_campaign_post(campaign_id):
    campaign = Campaign.query.get(campaign_id)

    if not campaign:
        flash("Campaign does not exist")
        return redirect(url_for("sponsor_home"))
    
    name = request.form.get('name')
    description = request.form.get('description')
    start_date = request.form.get('start_date')  
    end_date = request.form.get('end_date')  
    budget = request.form.get('budget')  
    visibility = request.form.get('visibility')
    goals = request.form.get('goals')

    if not name or not description or not start_date or not end_date or not budget or not visibility or not goals:
        flash("Please fill out all the details")
        return redirect(url_for('edit_campaign', campaign_id))
    
    campaign.name = name
    campaign.description = description
    campaign.start_date = datetime.strptime(start_date, '%Y-%m-%d')
    campaign.end_date = datetime.strptime(end_date, '%Y-%m-%d')
    campaign.budget = budget
    campaign.visibility = visibility
    campaign.goals = goals

    db.session.commit()
    flash('Campaign Update Successfully')
    return redirect(url_for('sponsor_home'))



@app.route('/campaign/<int:campaign_id>/delete')
@auth_required
def delete_campaign(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        flash("Campaign Does Not Exist")
        return redirect(url_for("sponsor_home"))
    return render_template("/campaign/delete.html", campaign=campaign , user=user)




@app.route('/campaign/<int:campaign_id>/delete', methods=['POST'])
@auth_required
def delete_campaign_post(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)

    if not campaign:
        flash("Campaign Does Not Exist")
        return redirect(url_for("sponsor_home"))
    
    db.session.delete(campaign)
    db.session.commit()

    flash('Campaign Deleted Successfully')
    if user.user_type == 'sponsor':
        return redirect(url_for('sponsor_home'))
    else:
        return redirect(url_for('admin_campaign'))




@app.route('/campaign/<int:campaign_id>/request')
@sponsor_req
def view_requests(campaign_id):
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    request = AdRequest.query.filter_by(campaign=campaign).all()
    
    if not request:
        flash ("No Request Till Now")

    return render_template('/campaign/request.html', campaign=campaign, request=request, user=user)



@app.route('/campaign/<int:campaign_id>/request/<int:request_id>/accept', methods=['GET', 'POST'])
@sponsor_req
def accept_request(campaign_id, request_id):
    campaign = Campaign.query.get(campaign_id)
    request = AdRequest.query.get(request_id)

    if campaign and request:
        if request.campaign_id == campaign.id:  
            request.status = "Accepted"
            db.session.commit()
            flash("Request accepted successfully!")
            return redirect(url_for('view_requests', campaign_id=campaign_id))


    return redirect(url_for('view_requests', campaign_id=campaign_id))


@app.route('/campaign/<int:campaign_id>/request/<int:request_id>/decline', methods=['GET', 'POST'])
def decline_request(campaign_id, request_id):
    campaign = Campaign.query.get(campaign_id)
    request = AdRequest.query.get(request_id)

    if campaign and request:
        if request.campaign_id == campaign.id:  
            request.status = "Declined"
            
            db.session.commit()
            flash("Request declined successfully!")
            return redirect(url_for('view_requests', campaign_id=campaign_id))
        else:
            flash("Invalid request!")
    else:
        flash("Campaign or request not found!")

    return redirect(url_for('view_requests', campaign_id=campaign_id))



@app.route('/influencer/<int:influencer_id>/profile')
def view_influencer_profile(influencer_id):
    influencer = Influencer.query.get(influencer_id)
    user = User.query.get(session['user_id'])
    if influencer:
        return render_template('/sponsor/in_pro.html', influencer=influencer, user=user)
    


@app.route('/sponsor/search')
@sponsor_req
def search():
    niches = ['Gaming', 'Fitness', 'Music', 'Lifestyle', 'Sports', 'Food', 'Travel', 'Art', 'Education', 'DIY crafts']
    user = User.query.get(session['user_id'])

    return render_template("/sponsor/search.html", user=user , niches=niches)

@app.route('/sponsor/search', methods=['POST'])
@sponsor_req
def search_post():
     niches = ['Gaming', 'Fitness', 'Music', 'Lifestyle', 'Sports', 'Food', 'Travel', 'Art', 'Education', 'DIY crafts']
     
     user = User.query.get(session['user_id'])

     niche = request.form.get('niche')
     keywords = request.form.get('keywords')

     influencers = Influencer.query.filter(Influencer.niche.like(f'%{niche}%')).filter(
         Influencer.name.like(f'%{keywords}%'))
     
     return render_template('/sponsor/search.html', niches=niches, influencers=influencers, user=user)



@app.route('/sponsor/<int:campaign_id>/search_influencer')
@sponsor_req
def search_influencers(campaign_id):
    niches = ['Gaming', 'Fitness', 'Music', 'Lifestyle', 'Sports', 'Food', 'Travel', 'Art', 'Education', 'DIY crafts']
    user = User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)

    return render_template("/sponsor/search_influencer.html", user=user, campaign=campaign , niches=niches)



@app.route('/sponsor/<int:campaign_id>/search_influencer', methods=['POST'])
@sponsor_req
def search_influencers_post(campaign_id):
     niches = ['Gaming', 'Fitness', 'Music', 'Lifestyle', 'Sports', 'Food', 'Travel', 'Art', 'Education', 'DIY crafts']
     campaign = Campaign.query.get(campaign_id)
     user = User.query.get(session['user_id'])

     niche = request.form.get('niche')
     keywords = request.form.get('keywords')

     influencers = Influencer.query.filter(Influencer.niche.like(f'%{niche}%')).filter(
         Influencer.name.like(f'%{keywords}%'))
     
     return render_template('/sponsor/search_influencer.html', niches=niches, influencers=influencers, campaign=campaign, user=user)




@app.route('/sponsor/<int:campaign_id>/request_campaign/<int:influencer_id>', methods=['GET'])
@sponsor_req
def request_campaign(influencer_id, campaign_id):
  
  influencer = Influencer.query.get(influencer_id)
  user = User.query.get(session['user_id'])

  campaign = Campaign.query.get(campaign_id)

  return render_template('/sponsor/request_campaign.html', influencer=influencer, user=user, campaign=campaign)  


@app.route('/sponsor/<int:campaign_id>/transaction')
@sponsor_req
def payment_requests(campaign_id):
    user = User.query.get(session['user_id'])
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id, completed=True).all()
    campaign = Campaign.query.get(campaign_id)

    return render_template('/sponsor/transaction.html', user=user, ad_requests=ad_requests, campaign=campaign)






#----------------------------------------------------------#


#------------------------influencer_pages-------------------#
@app.route('/influencer/in_reg')
@influencer_req
def influencer_registration():
    user = User.query.get(session['user_id'])
    return render_template('/influencer/in_reg.html',user=user) 


@app.route('/influencer/in_reg', methods=['POST'])
@influencer_req
def influencer_registration_post():
    user = User.query.get(session['user_id'])
    name = request.form.get('name')
    category = request.form.get('category')
    bio = request.form.get('bio')
    followers = request.form.get('followers')
    niche = request.form.get('niche')
    activities = request.form.get('activities')

    if not followers or not activities:
        return flash("Please enter both Followers and Activities!")

    try:
        f = int(followers)
        a = int(activities)
        if a > 0:
            reach =  int(f / a) 
    except ValueError:
        return flash("Followers and Activities must be numbers!")
    
    new_influencer = Influencer(user_id = user.id, name=name,category=category,bio=bio,followers=followers,niche=niche,activities=activities,reach=reach)
    db.session.add(new_influencer)
    db.session.commit()
    session['influencer_id'] = new_influencer.id 

    return redirect(url_for('influencer_profile'))


@app.route('/influencer/profile')
@influencer_req
def influencer_profile():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.filter_by(user_id=user.id).first()
    flag = user.is_flagged
    
    if not flag:
        if influencer:
            
            total = AdRequest.query.filter_by(influencer_id=influencer.id).count()
            accept = AdRequest.query.filter_by(influencer_id=influencer.id, status='Accepted').count()
            declined = AdRequest.query.filter_by(influencer_id=influencer.id, status='Declined').count()
            pending = AdRequest.query.filter_by(influencer_id=influencer.id, status='Pending').count()

            labels = ['Total Request', ' Accepted', 'Declined', 'Pending']
            data = [total,accept,declined,pending]

            return render_template('/influencer/profile.html', user=user, influencer=influencer,
                                labels=labels , data=data)
        else:
            flash('Continue Registration')
            return redirect(url_for('influencer_registration'))
    else:
        total = AdRequest.query.filter_by(influencer_id=influencer.id).count()
        accept = AdRequest.query.filter_by(influencer_id=influencer.id, status='Accepted').count()
        declined = AdRequest.query.filter_by(influencer_id=influencer.id, status='Declined').count()
        pending = AdRequest.query.filter_by(influencer_id=influencer.id, status='Pending').count()

        labels = ['Total Request', ' Accepted', 'Declined', 'Pending']
        data = [total,accept,declined,pending]
        flash('You have been flagged by admin')
        return render_template('/influencer/profile.html', user=user, influencer=influencer,
                                labels=labels , data=data)



@app.route('/influencer')
@influencer_req
def influencer_home():
    user=User.query.get(session['user_id'])
    influencer = Influencer.query.filter_by(user_id=user.id).first()
    flag = user.is_flagged
    
    if not flag:
        if influencer:
            campaigns = Campaign.query.all()
            search_text = request.args.get('search_text') 
            if search_text:
                campaigns = Campaign.query.filter(Campaign.niche.ilike(f'%{search_text}%')).all()
                return render_template('/influencer/home.html',user=user, campaigns=campaigns)
            else:
                return render_template('/influencer/home.html',user=user, campaigns=campaigns)
        else:
            flash('Continue Registration')
            return redirect(url_for('influencer_registration'))
    else:
        return redirect(url_for('influencer_profile'))


@app.route('/influencer/update')
@influencer_req
def profile_update():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.get(session['influencer_id'])
    return render_template('/influencer/update.html', user=user, influencer=influencer)



@app.route('/influencer/update', methods=['POST'])
@influencer_req
def profile_update_post():
    influencer = Influencer.query.get(session['influencer_id'])
    name = request.form.get('name')
    category = request.form.get('category')
    bio = request.form.get('bio')
    followers = request.form.get('followers')
    niche = request.form.get('niche')
    activities = request.form.get('activities')

    if not name or not category or not bio or not followers or not niche or not activities:
        return flash("Please enter all the fields!")

    try:
        f = int(followers)
        a = int(activities)
        if a > 0:
            reach =  int(f / a) 
    except ValueError:
        return flash("Followers and Activities must be numbers!")
    
    influencer.name = name
    influencer.category = category
    influencer.bio = bio
    influencer.followers = followers
    influencer.niche = niche
    influencer.activities = activities
    influencer.reach = reach
    db.session.commit()
    flash('Profile Update Successfully')
    return redirect(url_for('influencer_profile'))   

    



@app.route('/influencer/<int:campaign_id>/request')
@is_req
def influencer_ad_request(campaign_id):
    user=User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    influencer = Influencer.query.get(session['influencer_id'])
    existing_request = AdRequest.query.filter_by(campaign_id=campaign.id, influencer_id=influencer.id ).first()

    if existing_request:
        flash('already responded')
    
    return render_template('/influencer/request.html', user=user, campaign = campaign, influencer=influencer)



@app.route('/influencer/<int:campaign_id>/request', methods=['POST'])
@is_req
def influencer_ad_request_post(campaign_id):
    user=User.query.get(session['user_id'])
    campaign = Campaign.query.get(campaign_id)
    influencer = Influencer.query.get(session['influencer_id'])

    if user.user_type== 'influencer':
        campaign = Campaign.query.get(campaign_id)
        influencer = Influencer.query.get(session['influencer_id'])

        status = request.form.get('status')
        requirements = request.form.get('requirements')
        messages = request.form.get('message')
        payment = request.form.get('payment')


        completed = False 
        is_private= False

        new_request = AdRequest(campaign_id=campaign.id, influencer_id=influencer.id, status=status, messages=messages, requirements=requirements,payment_amount=payment, is_private=is_private,completed=completed )
        db.session.add(new_request)
        db.session.commit()
        flash("Request Send Successfully")
        return redirect(url_for('influencer_home'))


    if user.user_type== 'sponsor':
        campaign = Campaign.query.get(campaign_id)
        influencer = Influencer.query.get(session['influencer_id'])

        status = request.form.get('status')
        requirements = request.form.get('requirements')
        messages = request.form.get('message')
        payment = request.form.get('payment')

        is_private= True

        new_request = AdRequest(campaign_id=campaign.id, influencer_id=influencer.id, status=status, messages=messages, requirements=requirements,payment_amount=payment, is_private=is_private )
        db.session.add(new_request)
        db.session.commit()
        flash("Request Send Successfully")
        return redirect(url_for('sponsor_home'))


@app.route('/influencer/response')
@influencer_req
def influencer_response():
    user = User.query.get(session['user_id'])
    influencer = Influencer.query.filter_by(user_id=user.id).first()
    flag = user.is_flagged
    
    if not flag:
        if influencer:
            requests = AdRequest.query.filter_by(influencer_id=influencer.id).all()  
            return render_template('/influencer/response.html',user=user, requests=requests)
        
        else:
            flash('Continue Registration')
            return redirect(url_for('influencer_registration'))
    else:
        return redirect(url_for('influencer_profile'))






@app.route('/influencer/response/<int:request_id>/<action>')
@influencer_req
def influencer_action(request_id, action):
    if action not in ("accept", "decline", "completed"):
        return "Invalid action", 400

    request = AdRequest.query.get(request_id)

    

    if action == "accept":
        request.status = 'Accepted'
    elif action == "decline":
        request.status = 'Declined'
    elif action == "completed":
        request.status = 'Accepted'
        request.completed = True  

    db.session.commit()

    flash(f"Request successfully {action.lower()}d!", 'success')
    return redirect(url_for('influencer_response'))





