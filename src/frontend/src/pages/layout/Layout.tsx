import { Outlet, Link } from "react-router-dom";

import styles from "./Layout.module.css";
import Logo from "../../assets/iom-white.svg";  

const Layout = () => {
    return (
        <div className={styles.layout}>
            <header className={styles.header} role={"banner"}>
                <div className={styles.headerContainer}>
                    <Link to="/" className={styles.headerTitleContainer}>
                        <img src={Logo} alt="IOM" className={styles.headerLogo} />
                        <h3 className={styles.headerTitle}>| Policies Navigator</h3>
                    </Link>
                    <h4 className={styles.headerRightText}>Prompt <a href="https://hrhandbook.iom.int/hr-policy-framework"
                                target="_blank"
                                style={{ color: 'rgba(255, 184, 28, 1)' }}> HR Rules</a>{' '}
                                , {' '}
                                <a
                                href="https://iomint.sharepoint.com/sites/DMSPortal/Instructions/Forms/AllItems.aspx"
                                target="_blank"
                                style={{ color: 'rgba(255, 184, 28, 1)' }} >
                                Admin Instructions
                                </a>, {' '}
                                <a
                                href="https://iomint.sharepoint.com/sites/DMSPortal/Manuals/Forms/AllItems.aspx"
                                target="_blank"
                                style={{ color: 'rgba(255, 184, 28, 1)' }} >
                                Manuals
                                </a> & {' '}
                                <a
                                href="https://governingbodies.iom.int/"
                                target="_blank"
                                style={{ color: 'rgba(255, 184, 28, 1)' }} >
                                Audit
                                </a></h4>
                </div>
            </header>

            <Outlet />
        </div>
    );
};

export default Layout;
