import mechanize
import ClientForm

class VMTN:
    addUrl = 'http://www.vmware.com/vmwarestore/newstore/community_login.jsp?followingPage=http://www.vmware.com/vmtn/appliances/directory/create_community_appliance'

    editUrl = 'http://www.vmware.com/vmwarestore/newstore/community_login.jsp?www.vmware.com/vmtn/appliances/directory/'

    baseUrl = 'http://www.vmware.com/vmtn/appliances/directory/'

    def login(self, user, password, url):
        res = mechanize.urlopen(url)

        forms = ClientForm.ParseResponse(res, backwards_compat=False)

        for form in forms:
            try:
                form.find_control('Email')
                loginForm = form
                break
            except:
                pass

        loginForm['Email'] = user
        loginForm['Password'] = password
        return mechanize.urlopen(loginForm.click())

    def editEntry(self, form, data):
        form['edit[title]']             = data['title'] # title (max 128 chars)
        form['edit[flexinode_8]']       = data['oneLiner'] # one line desc (max 128 chars)
        form['edit[flexinode_2]']       = data['url'] # download link
        form['edit[flexinode_1]']       = data['longDesc'] #long Description

        form['edit[flexinode_59year]']  = [str(data['year'])] # year 
        form['edit[flexinode_59month]'] = [str(data['month'])] # Day of month (1-31)
        form['edit[flexinode_59day]']   = [str(data['day'])] # hour of day
        form['edit[flexinode_59hour]']  = [str(data['hour'])] # hour of day
        form['edit[flexinode_59minute]']= [str(data['minute'])]

        form['edit[flexinode_12]']      = data['os'] # os and version
        form['edit[flexinode_16]']      = data['userName'] # appliance username
        form['edit[flexinode_47]']      = data['password'] # Password
        form['edit[flexinode_11]']      = str(data['memory']) #allocated mem 
        form['edit[flexinode_3]']       = str(data['size']) # size compressed

        # VMTN has two inputs for torrent and vmtools (checkboxes) that cause 
        # exceptions in ClientForm.  This is a work-around. 
        # ClientForm also needs to be patched to allow multiple inputs with the
        # same name,
        # or it will choke on vmware's submission page.
        for control in form.controls:
            if control.name == 'edit[flexinode_5]':
                if type(control.value) == list and data['torrent'] == '1':
                    control.value = [data['torrent']]
        for control in form.controls:
            if control.name == 'edit[flexinode_7]':
                if type(control.value) == list and data['vmtools'] == '1':
                    control.value = [data['vmtools']]
                
        return mechanize.urlopen(form.click())
     
    def add(self, user, password, data):
        res = self.login(user, password, self.addUrl)
        forms = ClientForm.ParseResponse(res, backwards_compat=False)
        for form in forms:
            try:
                form.find_control('edit[title]')
                break
            except ClientForm.ControlNotFoundError:
                pass

        res = self.editEntry(form, data)
        return res._url.split('/')[-1]

    def edit(self, user, password, data, vmtnId):
        self.login(user, password, self.editUrl)
        res = mechanize.urlopen(self.baseUrl + str(vmtnId) + '/edit')
        forms = ClientForm.ParseResponse(res, backwards_compat=False)
        for form in forms:
            try:
                form.find_control('edit[title]')
                break
            except ClientForm.ControlNotFoundError:
                pass
        self.editEntry(form, data)
